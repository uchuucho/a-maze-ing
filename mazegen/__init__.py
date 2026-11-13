"""mazegen: reusable maze generator.

Usage:
    from mazegen import MazeGenerator

    gen = MazeGenerator(20, 15, entry=(0, 0), exit=(14, 19),
                        perfect=True, seed=42, algorithm="dfs")
    gen.generate()        # build the maze
    gen.grid              # rows of ints; bits = walls (N=1 E=2 S=4 W=8)
    gen.blocked           # cells of the '42' pattern
    gen.solve()           # shortest path: list of (row, col)
    gen.save("maze.txt")  # write the output file
"""
from .generator import MazeGenerator

__all__ = ["MazeGenerator"]