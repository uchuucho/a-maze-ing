"""Reusable maze generation module.

Provides the MazeGenerator class, which builds, solves and exports
mazes without any display code, so it can be imported by other projects.

Cells are addressed as (row, col). Each cell is stored as an int whose
4 low bits encode its walls (0 = open, 1 = closed):

    bit 0 (1) = North, bit 1 (2) = East, bit 2 (4) = South, bit 3 (8) = West
"""
import random
from collections import deque
from typing import Callable, Optional


Cell = tuple[int, int]  # (row, col)

# called as animation_step(a, b) after each wall opened between a and b
AnimationStep = Optional[Callable[[Cell, Cell], None]]

# walls (0->open, 1->closed)
N, E, S, W = 1, 2, 4, 8

# directions (row change, col change, opposite bit)
DIRS: dict[int, tuple[int, int, int]] = {
    N: (-1, 0, S),
    E: (0, 1, W),
    S: (1, 0, N),
    W: (0, -1, E),
}

# move between two cells -> letter used in the output file
LETTERS: dict[tuple[int, int], str] = {
    (-1, 0): "N", (0, 1): "E", (1, 0): "S", (0, -1): "W",
}

# '42' pattern as (row, col) offsets from its top-left corner
# perfect mode: 4 rows x 6 cols
_PFOUR = {(0, 0), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2), (3, 2)}
_PTWO = {(0, 4), (0, 5), (1, 5), (2, 4), (3, 4), (3, 5)}
# non-perfect mode: 6 rows x 6 cols (no dead-end pockets)
_NDEFOUR = {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2), (4, 2), (5, 2)}
_NDETWO = {(0, 4), (0, 5), (1, 5), (2, 5), (3, 4), (4, 4), (5, 4), (5, 5)}


class MazeGenerator:
    """Generate, solve and export a maze.

    Attributes:
        width: Number of columns.
        height: Number of rows.
        entry: Entry cell as (row, col).
        exit: Exit cell as (row, col).
        perfect: If True, exactly one path between any two cells.
        rng: Random generator, seeded for reproducibility.
        grid: One int per cell; its 4 low bits are the walls.
        blocked: Cells that form the '42' pattern (never opened).

    Example:
        >>> gen = MazeGenerator(20, 15, (0, 0), (14, 19), seed=42)
        >>> gen.generate()
        >>> path = gen.solve()
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: Cell,
        exit: Cell,
        perfect: bool = False,
        seed: Optional[int] = None,
        algorithm: str = "dfs",
    ) -> None:
        """Store the settings and create a grid with every wall closed.

        Args:
            width: Number of columns.
            height: Number of rows.
            entry: Entry cell as (row, col).
            exit: Exit cell as (row, col).
            perfect: Build a perfect maze if True.
            seed: Seed for reproducible mazes; None gives a random maze.
            algorithm: Generation algorithm: "dfs", "prim", "kruskal"
                or "hunt_and_kill".
        """
        self.width = width
        self.height = height
        self.entry = entry
        self.exit = exit
        self.perfect = perfect
        self.algorithm = algorithm
        self.rng = random.Random(seed)
        # 15 = 0b1111: all four walls closed
        self.grid: list[list[int]] = [
            [15] * width for _ in range(height)
        ]
        # set of cells that make up the 42 pattern
        self.blocked: set[Cell] = set()

    def add42(self) -> None:
        """Mark the '42' pattern cells as blocked, near the maze centre.

        The pattern never covers the entry or the exit, and in
        non-perfect mode it leaves the centre cell open. If the maze is
        too small, an error message is printed and no cell is blocked.
        """
        (enr, enc) = self.entry
        (exr, exc) = self.exit
        if self.perfect:
            shape = _PFOUR | _PTWO
            if self.width < 8 or self.height < 6:
                print("Error: maze too small for the '42' pattern")
                return None
            ih, iw = 0, 0
            for i in range(1, self.height):
                if 2 * (i + 2) > self.height or i + 5 > self.height:
                    break
                for j in range(1, self.width):
                    if 2 * (j + 3) > self.width or j + 7 > self.width:
                        break
                    if (enr - i, enc - j) in shape:
                        continue
                    if (exr - i, exc - j) in shape:
                        continue
                    ih, iw = i, j
        else:
            shape = _NDEFOUR | _NDETWO
            center = (self.height // 2, self.width // 2)
            if self.width < 8 or self.height < 8:
                print("Error: maze too small for the '42' pattern")
                return None
            ih, iw = 0, 0
            for i in range(1, self.height):
                if 2 * (i + 2) >= self.height or i + 7 > self.height:
                    break
                for j in range(1, self.width):
                    if 2 * (j + 3) > self.width or j + 7 > self.width:
                        break
                    if (enr - i, enc - j) in shape:
                        continue
                    if (exr - i, exc - j) in shape:
                        continue
                    if (center[0] - i, center[1] - j) in shape:
                        continue
                    ih, iw = i, j
        if (ih, iw) == (0, 0):
            print("Error: maze too small for the '42' pattern")
            return None
        self.blocked = {(ih + i, iw + j) for (i, j) in shape}

    def _open(self, a: Cell, b: Cell) -> None:
        """Remove the wall between two neighbouring cells.

        Both cells are updated, so the shared wall stays coherent.

        Args:
            a: First cell as (row, col).
            b: Second cell, next to a.
        """
        dr, dc = b[0] - a[0], b[1] - a[1]
        for bit, (ir, ic, opp) in DIRS.items():
            if (ir, ic) == (dr, dc):
                self.grid[a[0]][a[1]] &= ~bit
                self.grid[b[0]][b[1]] &= ~opp
                return

    def _neighbours(self, cell: Cell) -> list[Cell]:
        """List the cells next to cell that can be opened.

        Args:
            cell: A cell as (row, col).

        Returns:
            Adjacent cells inside the maze that are not part of the '42'.
        """
        r, c = cell
        result: list[Cell] = []
        for ir, ic, _ in DIRS.values():
            nr, nc = r + ir, c + ic
            inside = 0 <= nr < self.height and 0 <= nc < self.width
            if inside and (nr, nc) not in self.blocked:
                result.append((nr, nc))
        return result

    def _dfs(self, animation_step: AnimationStep = None) -> None:
        """Carve a perfect maze with a randomized depth-first search.

        Starts at the entry, walks to a random unvisited neighbour,
        and backtracks when stuck, until every reachable cell is visited.

        Args:
            animation_step: Optional function called as animation_step(a, b) after
                each wall opened between cells a and b (for animation).
        """
        visited: set[Cell] = {self.entry}
        stack: list[Cell] = [self.entry]
        while stack:
            cur = stack[-1]
            options = [n for n in self._neighbours(cur) if n not in visited]
            if not options:
                stack.pop()  # dead-end: backtrack
                continue
            nxt = self.rng.choice(options)
            self._open(cur, nxt)
            if animation_step:
                animation_step(cur, nxt)
            visited.add(nxt)
            stack.append(nxt)

    def _prim(self, animation_step: AnimationStep = None) -> None:
        """Carve a perfect maze with a randomized Prim's algorithm.

        Grows the maze from the entry: repeatedly takes a random frontier
        cell (next to the maze but not in it yet) and connects it to a
        random neighbour that is already in the maze.

        Args:
            animation_step: Optional function called as
                animation_step(a, b) after each wall opened between
                cells a and b (for animation).
        """
        in_maze: set[Cell] = set()
        frontier: list[Cell] = [self.entry]
        queued: set[Cell] = {self.entry}
        while frontier:
            # take a random frontier cell (swap with last, then pop)
            i = self.rng.randrange(len(frontier))
            frontier[i], frontier[-1] = frontier[-1], frontier[i]
            cur = frontier.pop()
            links: list[Cell] = []
            for n in self._neighbours(cur):
                if n in in_maze:
                    links.append(n)
                elif n not in queued:
                    queued.add(n)
                    frontier.append(n)
            if links:
                nxt = self.rng.choice(links)
                self._open(cur, nxt)
                if animation_step:
                    animation_step(cur, nxt)
            in_maze.add(cur)

    def _kruskal(self, animation_step: AnimationStep = None) -> None:
        """Carve a perfect maze with a randomized Kruskal's algorithm.

        Every cell starts in its own group. Walls between neighbours are
        taken in random order; a wall is opened only if it joins two
        different groups, so no loop is ever created.

        Args:
            animation_step: Optional function called as
                animation_step(a, b) after each wall opened between
                cells a and b (for animation).
        """
        group: dict[Cell, Cell] = {}
        walls: list[tuple[Cell, Cell]] = []
        for r in range(self.height):
            for c in range(self.width):
                if (r, c) in self.blocked:
                    continue
                group[(r, c)] = (r, c)
                # east and south only, so each wall is listed once
                for n in self._neighbours((r, c)):
                    if n > (r, c):
                        walls.append(((r, c), n))
        self.rng.shuffle(walls)

        def find(cell: Cell) -> Cell:
            """Return the representative of the cell's group."""
            while group[cell] != cell:
                cell = group[cell]
            return cell

        for a, b in walls:
            root_a, root_b = find(a), find(b)
            if root_a == root_b:
                continue  # already connected: opening would make a loop
            group[root_a] = root_b
            self._open(a, b)
            if animation_step:
                animation_step(a, b)

    def _hunt_and_kill(self, animation_step: AnimationStep = None) -> None:
        """Carve a perfect maze with the hunt-and-kill algorithm.

        Kill: walk randomly into unvisited cells until stuck.
        Hunt: scan the grid for an unvisited cell next to a visited one,
        connect them, and start walking again from there.

        Args:
            animation_step: Optional function called as
                animation_step(a, b) after each wall opened between
                cells a and b (for animation).
        """
        visited: set[Cell] = {self.entry}
        cur: Optional[Cell] = self.entry
        while cur is not None:
            # kill: random walk
            options = [n for n in self._neighbours(cur) if n not in visited]
            if options:
                nxt = self.rng.choice(options)
                self._open(cur, nxt)
                if animation_step:
                    animation_step(cur, nxt)
                visited.add(nxt)
                cur = nxt
                continue
            # hunt: first unvisited cell that touches the visited area
            cur = None
            for r in range(self.height):
                for c in range(self.width):
                    cell = (r, c)
                    if cell in visited or cell in self.blocked:
                        continue
                    links = [n for n in self._neighbours(cell)
                             if n in visited]
                    if links:
                        nxt = self.rng.choice(links)
                        self._open(cell, nxt)
                        if animation_step:
                            animation_step(cell, nxt)
                        visited.add(cell)
                        cur = cell
                        break
                if cur is not None:
                    break

    def _is_dead_end(self, cell: Cell) -> bool:
        """Return True if cell is a corridor cell with exactly 3 walls."""
        r, c = cell
        return cell not in self.blocked and self.grid[r][c] in (7, 11, 13, 14)

    def _reachable_neighbours(self, cell: Cell) -> list[Cell]:
        """List the neighbours reachable from cell (no wall between)."""
        r, c = cell
        return [
            (r + ir, c + ic) for bit, (ir, ic, _) in DIRS.items()
            if not self.grid[r][c] & bit
        ]

    def _is_wide_corridor(self, top: int, left: int) -> bool:
        """Return True if the 3x3 square at (top, left) has no inner wall."""
        if top < 0 or left < 0:
            return False
        if top + 3 > self.height or left + 3 > self.width:
            return False
        for r in range(top, top + 3):
            for c in range(left, left + 3):
                if c < left + 2 and self.grid[r][c] & E:
                    return False
                if r < top + 2 and self.grid[r][c] & S:
                    return False
        return True

    def _makes_wide_corridor(self, a: Cell, b: Cell) -> bool:
        """Return True if opening the wall a-b would create a wide corridor.

        Opens the wall, checks every 3x3 square that contains both
        cells, then closes the wall again.
        """
        before_a = self.grid[a[0]][a[1]]
        before_b = self.grid[b[0]][b[1]]
        self._open(a, b)
        found = False
        for top in range(max(a[0], b[0]) - 2, min(a[0], b[0]) + 1):
            for left in range(max(a[1], b[1]) - 2, min(a[1], b[1]) + 1):
                if self._is_wide_corridor(top, left):
                    found = True
        self.grid[a[0]][a[1]] = before_a
        self.grid[b[0]][b[1]] = before_b
        return found

    def _remove_dead_ends(self, animation_step: AnimationStep = None) -> None:
        """Remove dead-ends by opening one extra wall in each of them.

        This adds loops, turning the perfect maze into a board with
        several routes. A wall is never opened if it would create a
        corridor wider than 2 cells. Passes repeat until nothing changes.

        Args:
            animation_step: Optional function called as
                animation_step(a, b) after each wall opened between
                cells a and b (for animation).
        """
        changed = True
        while changed:
            changed = False
            for r in range(self.height):
                for c in range(self.width):
                    cell = (r, c)
                    if not self._is_dead_end(cell):
                        continue
                    # closed walls we may open
                    options = [
                        n for n in self._neighbours(cell)
                        if n not in self._reachable_neighbours(cell)
                        and not self._makes_wide_corridor(cell, n)
                    ]
                    if not options:
                        continue
                    # prefer a neighbour that is also a dead-end
                    twins = [n for n in options if self._is_dead_end(n)]
                    nxt = self.rng.choice(twins or options)
                    self._open(cell, nxt)
                    if animation_step:
                        animation_step(cell, nxt)
                    changed = True

    def generate(self, animation_step: AnimationStep = None) -> None:
        """Build a new maze in self.grid.

        Closes every wall, places the '42' pattern, then carves the maze
        with the chosen algorithm and in non-perfect mode, removes dead-ends.

        Args:
            animation_step: Optional function called as
                animation_step(a, b) after each wall opened between
                cells a and b (for animation).

        Raises:
            ValueError: If the algorithm name is unknown.
        """
        algorithms = {
            "dfs": self._dfs,
            "prim": self._prim,
            "kruskal": self._kruskal,
            "hunt_and_kill": self._hunt_and_kill,
        }
        if self.algorithm not in algorithms:
            raise ValueError(
                f"unknown algorithm '{self.algorithm}' "
                f"(use one of: {', '.join(algorithms)})"
            )
        self.grid = [[15] * self.width for _ in range(self.height)]
        self.blocked = set()
        self.add42()
        algorithms[self.algorithm](animation_step)
        if not self.perfect:
            self._remove_dead_ends(animation_step)

    def solve(self) -> list[Cell]:
        """Find the shortest path from the entry to the exit (BFS).

        Returns:
            The cells of the path, from entry to exit included, or an
            empty list if the exit cannot be reached.
        """
        came_from: dict[Cell, Cell] = {self.entry: self.entry}
        queue: deque[Cell] = deque([self.entry])
        while queue:
            cur = queue.popleft()
            if cur == self.exit:
                break
            for n in self._reachable_neighbours(cur):
                if n not in came_from:
                    came_from[n] = cur
                    queue.append(n)
        if self.exit not in came_from:
            return []
        path = [self.exit]
        while path[-1] != self.entry:
            path.append(came_from[path[-1]])
        path.reverse()
        return path

    def to_hex(self) -> str:
        """Return the maze in the output file format.

        One hex digit per cell (row by row), an empty line, then the
        entry, the exit and the shortest path as N/E/S/W letters.
        """
        lines = [
            "".join(format(cell, "X") for cell in row) for row in self.grid
            ]
        path = self.solve()
        moves = "".join(
            LETTERS[(b[0] - a[0], b[1] - a[1])]
            for a, b in zip(path, path[1:])
        )
        lines.append("")
        lines.append(f"{self.entry[0]},{self.entry[1]}")
        lines.append(f"{self.exit[0]},{self.exit[1]}")
        lines.append(moves)
        return "\n".join(lines) + "\n"

    def save(self, filename: str) -> None:
        """Write the maze to filename in the output file format.

        Args:
            filename: Path of the file to write.

        Raises:
            OSError: If the file cannot be written.
        """
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.to_hex())
