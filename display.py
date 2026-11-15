"""Terminal display for a MazeGenerator maze.

The maze is drawn on a canvas of square pixels: each cell is CELL x CELL
pixels and each wall is one pixel thick. Two pixel rows share one
terminal character, drawn as an upper half block (top pixel = text
color, bottom pixel = background color).
"""
import sys

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


class Canvas:
    """Pixel picture of a maze, drawn in the terminal.

    Every pixel stores a kind ("wall", "floor", "42", ...) and the
    palette turns kinds into colors, so changing a color only means
    changing the palette and redrawing.

    Attributes:
        gen: The generator whose maze is drawn.
        cell_size: Size of a cell in pixels.
        palette: Color of each pixel kind.
        kinds: Kind of every pixel, row by row (wall, floor, 42, entry, exit, path, head).
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