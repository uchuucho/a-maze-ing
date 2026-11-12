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

# wall (0->open, 1->closed)
N, E, S, W = 1, 2, 4, 8

# directions (row change, col change, opposite bit)
DIRS: dict[int, tuple[int, int, int]] = {
    N: (-1, 0, S),
    E: (0, 1, W),
    S: (1, 0, N),
    W: (0, -1, E),
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
        perfect: bool = True,
        seed: Optional[int] = None,
    ) -> None:
        """Store the settings and create a grid with every wall closed.

        Args:
            width: Number of columns.
            height: Number of rows.
            entry: Entry cell as (row, col).
            exit: Exit cell as (row, col).
            perfect: Build a perfect maze if True.
            seed: Seed for reproducible mazes; None gives a random maze.
        """
        self.width = width
        self.height = height
        self.entry = entry
        self.exit = exit
        self.perfect = perfect
        self.rng = random.Random(seed)
        # 15 = 0b1111: all four walls closed
        self.grid: list[list[int]] = [
            [15] * width for _ in range(height)
        ]
        self.blocked: set[Cell] = set()

    def add42(self) -> None:
        """Mark the '42' pattern cells as blocked, near the maze centre.

        The pattern never covers the entry or the exit. If the maze is
        too small, an error message is printed and no cell is blocked.
        """
        (enr, enc) = self.entry
        (exr, exc) = self.exit
        if self.perfect:
            shape = _PFOUR | _PTWO
            if self.width < 8 or self.height < 6:
                print("Error: maze too small for the '42' pattern")  # new
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
            if self.width < 8 or self.height < 8:
                print("Error: maze too small for the '42' pattern")  # new
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
                    ih, iw = i, j
        if (ih, iw) == (0, 0):
            print("Error: maze too small for the '42' pattern")  # new
            return None
        self.blocked = {(ih + i, iw + j) for (i, j) in shape}