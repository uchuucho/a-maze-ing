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

# wall (0->open, 1->close)
N, E, S, W = 1, 2, 4, 8

# directions (row change, col change, opposite bit)
DIRS: dict[int, tuple[int, int, int]] = {
    N: (-1, 0, S),
    E: (0, 1, W),
    S: (1, 0, N),
    W: (0, -1, E),
}


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
