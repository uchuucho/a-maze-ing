"""Terminal display for a MazeGenerator maze.

The maze is drawn on a canvas of square pixels: each cell is CELL x CELL
pixels and each wall is one pixel thick. Two pixel rows share one
terminal character, drawn as an upper half block (top pixel = text
color, bottom pixel = background color).
"""
import sys
import shutil
import time
import math
import random
from mazegen import MazeGenerator
from mazegen.generator import E, S

Color = tuple[int, int, int]
Cell = tuple[int, int]
# (first row, last row, first col, last col)
Box = tuple[int, int, int, int]

PALETTE: dict[str, Color] = {
    "floor": (18, 18, 22),
    "wall": (98, 92, 128),
    "42": (167, 139, 250),
    "entry": (80, 250, 170),
    "exit": (255, 184, 108),
    "path": (255, 121, 198),
    "head": (80, 250, 170),
}
WALL_COLORS: list[Color] = [
    (98, 92, 128), (140, 140, 150), (70, 110, 150), (130, 80, 110),
]
SOFT = "~" 
SOFTNESS = 0.45  # SOFT and SOFTNESS are used to get the rounded corners

# explosion colors, from first frame to last (white-hot -> fading out)
EXPLOSION: list[Color] = [
    (255, 255, 255), (255, 200, 235), (255, 121, 198),
    (210, 90, 200), (167, 139, 250), (60, 50, 90),
]


class Canvas:
    """Pixel picture of a maze, drawn in the terminal.

    Every pixel stores a kind ("wall", "floor", "42", ...) and the
    palette turns kinds into colors, so changing a color only means
    changing the palette and redrawing.

    Attributes:
        gen: The generator whose maze is drawn.
        cell_size: Size of a cell in pixels.
        palette: Color of each pixel kind.
        kinds: Kind of every pixel, row by row ("wall", "floor", "42",
            "entry", "exit", "path", "head").
    """

    def __init__(self, gen: MazeGenerator, cell_size: int = 6) -> None:
        """Create an empty canvas sized for the generator's maze.

        Args:
            gen: The generator whose maze is drawn.
            cell_size: Size of a cell in pixels.
        """
        self.gen = gen
        self.cell_size = cell_size
        self.step = cell_size + 1
        self.rows = self.step * gen.height + 1
        self.cols = self.step * gen.width + 1
        self.palette = dict(PALETTE)
        self.kinds: list[list[str]] = []

    def cell_box(self, cell: Cell) -> Box:
        """Return the pixel box inside a cell (its walls excluded)."""
        r, c = cell
        return (self.step * r + 1, self.step * r + self.cell_size,
                self.step * c + 1, self.step * c + self.cell_size)

    def wall_box(self, a: Cell, b: Cell) -> Box:
        """Return the pixel box of the wall between two neighbors."""
        if a[0] == b[0]:  # same row: vertical wall
            j = self.step * max(a[1], b[1])
            i0, i1, _, _ = self.cell_box(a)
            return (i0, i1, j, j)
        i = self.step * max(a[0], b[0])
        _, _, j0, j1 = self.cell_box(a)
        return (i, i, j0, j1)

    def fill(self, box: Box, kind: str) -> None:
        """Set every pixel of box to kind, without drawing."""
        i0, i1, j0, j1 = box
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                self.kinds[i][j] = kind

    def tile(self, cell: Cell, kind: str, size: int) -> Box:
        """Put a rounded square of kind in the middle of a cell.

        The cell is cleared to floor first. Returns the cell's box.
        """
        box = self.cell_box(cell)
        self.fill(box, "floor")
        i0, _, j0, _ = box
        off = (self.cell_size - size) // 2
        top, left = i0 + off, j0 + off
        bottom, right = top + size - 1, left + size - 1
        self.fill((top, bottom, left, right), kind)
        if size >= 5:  # soften the four corners
            for i, j in ((top, left), (top, right),
                         (bottom, left), (bottom, right)):
                self.kinds[i][j] = kind + SOFT
        return box

    def rebuild(self) -> None:
        """Recompute every pixel from the generator's current maze."""
        gen = self.gen
        self.kinds = [["wall"] * self.cols for _ in range(self.rows)]
        for r in range(gen.height):
            for c in range(gen.width):
                if (r, c) in gen.blocked:
                    self.tile((r, c), "42", self.cell_size)
                    continue
                self.fill(self.cell_box((r, c)), "floor")
                if c + 1 < gen.width and not gen.grid[r][c] & E:
                    self.fill(self.wall_box((r, c), (r, c + 1)), "floor")
                if r + 1 < gen.height and not gen.grid[r][c] & S:
                    self.fill(self.wall_box((r, c), (r + 1, c)), "floor")
        self.tile(gen.entry, "entry", self.cell_size)
        self.tile(gen.exit, "exit", self.cell_size)

    def color(self, i: int, j: int,
              over: dict[tuple[int, int], Color] | None = None) -> Color:
        """Return the color of pixel (i, j), or its override if any."""
        if over and (i, j) in over:
            return over[(i, j)]
        kind = self.kinds[i][j]
        if kind.endswith(SOFT):
            a = self.palette[kind[:-1]]
            b = self.palette["floor"]
            return (round(a[0] * SOFTNESS + b[0] * (1 - SOFTNESS)),
                    round(a[1] * SOFTNESS + b[1] * (1 - SOFTNESS)),
                    round(a[2] * SOFTNESS + b[2] * (1 - SOFTNESS)))
        return self.palette[kind]

    def chars(self, box: Box,
              over: dict[tuple[int, int], Color] | None = None) -> str:
        """Return the escape codes that redraw the characters of box."""
        i0, i1, j0, j1 = box
        out: list[str] = []
        for top in range(i0 - i0 % 2, i1 + 1, 2):
            out.append(f"\x1b[{top // 2 + 1};{j0 + 1}H")
            for j in range(j0, j1 + 1):
                r1, g1, b1 = self.color(top, j, over)
                out.append(f"\x1b[38;2;{r1};{g1};{b1}m")
                if top + 1 < self.rows:
                    r2, g2, b2 = self.color(top + 1, j, over)
                    out.append(f"\x1b[48;2;{r2};{g2};{b2}m▀")
                else:
                    out.append("\x1b[49m▀")
        return "".join(out) + "\x1b[0m"

    def draw(self) -> None:
        """Clear the screen and draw the whole canvas."""
        whole = (0, self.rows - 1, 0, self.cols - 1)
        sys.stdout.write("\x1b[2J\x1b[?25l" + self.chars(whole))
        sys.stdout.flush()

    def show(self, box: Box) -> None:
        """Redraw only the part of the screen covered by box."""
        sys.stdout.write(self.chars(box))
        sys.stdout.flush()

    def link_box(self, a: Cell, b: Cell) -> Box:
        """Return the 1-pixel line joining the centers of two neighbors."""
        off = 1 + (self.cell_size - 1) // 2
        return (self.step * min(a[0], b[0]) + off,
                self.step * max(a[0], b[0]) + off,
                self.step * min(a[1], b[1]) + off,
                self.step * max(a[1], b[1]) + off)

    def show_path(self, visible: bool, delay: float = 0.0) -> None:
        """Draw the shortest path as a thin line, or erase it.

        Args:
            visible: True to draw the path, False to erase it.
            delay: Seconds between two segments (to animate the drawing).
        """
        path = self.gen.solve()
        kind = "path" if visible else "floor"
        for a, b in zip(path, path[1:]):
            box = self.link_box(a, b)
            self.fill(box, kind)
            self.show(box)
            time.sleep(delay)
        for cell, tile_kind in ((self.gen.entry, "entry"),
                                (self.gen.exit, "exit")):
            self.show(self.tile(cell, tile_kind, self.cell_size))

    def set_wall_color(self, color: Color) -> None:
        """Change the wall color and redraw the whole maze.

        Args:
            color: The new wall color as (R, G, B).
        """
        self.palette["wall"] = color
        self.draw()

    def explode(self, cell: Cell, frames: int = 80,
                particles: int = 500, delay: float = 0.03) -> None:
        """Play a firework centered on cell; the maze is left unchanged.

        Args:
            cell: Where the firework starts.
            frames: Number of animation frames.
            particles: Number of particles.
            delay: Seconds between frames.
        """
        i0, i1, j0, j1 = self.cell_box(cell)
        cy, cx = (i0 + i1) / 2, (j0 + j1) / 2
        speeds: list[tuple[float, float]] = []
        for _ in range(particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.6, 2.2)
            speeds.append((math.cos(angle) * speed, math.sin(angle) * speed))
        shown: set[tuple[int, int]] = set()
        for t in range(frames):
            color = EXPLOSION[t * len(EXPLOSION) // frames]
            over: dict[tuple[int, int], Color] = {}
            for vx, vy in speeds:
                y, x = round(cy + vy * t), round(cx + vx * t)
                if 0 <= y < self.rows and 0 <= x < self.cols:
                    over[(y, x)] = color
            now = {(y - y % 2, x) for y, x in over}
            # redraw last frame's spots (now empty) and this frame's spots
            sys.stdout.write("".join(
                self.chars((y, y, x, x), over) for y, x in shown | now))
            sys.stdout.flush()
            shown = now
            time.sleep(delay)
        sys.stdout.write("".join(self.chars((y, y, x, x)) for y, x in shown))
        sys.stdout.flush()


class Animator:
    """Draw the maze while the generator builds it."""

    def __init__(self, canvas: Canvas, delay: float = 0.02) -> None:
        """Store the canvas and the pause between frames.

        Args:
            canvas: The canvas to draw on.
            delay: Seconds to wait after each opened wall.
        """
        self.canvas = canvas
        self.delay = delay
        self.started = False
        self.head: Cell | None = None

    def step(self, a: Cell, b: Cell) -> None:
        """Show one opened wall (passed to gen.generate)."""
        canvas = self.canvas
        if not self.started:
            canvas.rebuild()  # '42' is placed, all walls still closed
            canvas.draw()
            self.started = True
        if self.head is not None:
            canvas.fill(canvas.cell_box(self.head), "floor")
            canvas.show(canvas.cell_box(self.head))
        canvas.fill(canvas.wall_box(a, b), "floor")
        canvas.fill(canvas.cell_box(a), "floor")
        box = canvas.tile(b, "head", max(canvas.cell_size - 2, 1))
        for part in (canvas.wall_box(a, b), canvas.cell_box(a), box):
            canvas.show(part)
        self.head = b
        time.sleep(self.delay)


def generate(canvas: Canvas, animate: bool = True,
             delay: float = 0.06) -> None:
    """Generate a new maze (animated or not), then draw the final state.

    Args:
        canvas: The canvas whose generator builds the maze.
        animate: Show the maze being built if True.
        delay: Seconds between animation frames.
    """
    if animate:
        canvas.gen.generate(Animator(canvas, delay).step)
    else:
        canvas.gen.generate()
    canvas.rebuild()
    canvas.draw()


def fit_cell_size(width: int, height: int, wanted: int) -> int:
    """Return the largest cell size, up to wanted, that fits the terminal.

    Args:
        width: Maze width in cells.
        height: Maze height in cells.
        wanted: Preferred cell size (the maximum to try).

    Returns:
        The cell size to use, or 0 if the maze does not fit at all.
    """
    cols, lines = shutil.get_terminal_size()
    lines -= 4  # keep room for the legend and menu under the maze
    for size in range(wanted, 0, -1):
        step = size + 1
        if step * width + 1 <= cols and (step * height + 2) // 2 <= lines:
            return size
    return 0


def legend(canvas: Canvas) -> str:
    """Return a one-line color legend for the maze.

    Args:
        canvas: The canvas whose current colors are shown.
    """
    names = [("wall", "wall"), ("entry", "entry"), ("exit", "exit"),
             ("path", "shortest path"), ("42", "42 pattern")]
    items = []
    for kind, label in names:
        r, g, b = canvas.palette[kind]
        items.append(f"\x1b[48;2;{r};{g};{b}m  \x1b[0m {label}")
    return "   ".join(items)
