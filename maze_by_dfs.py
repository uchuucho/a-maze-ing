from maze_config_creation import Maze, MazeConfig, Pixel
from utils import paint_wall, paint_cell, remove_dead_ends
import random
import sys
import time


# binary location: 0bWSEN -> 1 wall 0 no wall
N, E, S, W = 1, 2, 4, 8
# directions: (row, col, opposite_dir)
DIRS = {N: (-1, 0, S), E: (0, 1, W), S: (1, 0, N), W: (0, -1, E)}

# colors
BG = (10, 50, 60)        # cell background
WALL = (224, 163, 78)       # wall
HEAD = (98, 252, 3)     # the cell DFS is standing on
TRAIL = (120, 80, 40)    # in the stack, waiting

PATH = (255, 240, 200)     # shortest path
START = (235, 7, 7)     # entry 
END = (10, 140, 12)     # exit


def dfs_generator(maze: Maze, delay: float = 0.03) -> None:

    random.seed(maze.config.seed)

    wd = maze.config.width
    ht = maze.config.height
    cell = maze.config.cell

    done: set[tuple[int, int]] = {maze.config.entry}
    stack: list[tuple[int, int]] = [maze.config.entry]

    paint_cell(maze, *maze.config.entry, Pixel(HEAD, 0b0000))
    time.sleep(delay)

    while stack:
        r, c = stack[-1]
        neighbors = [
            (bit, r + ir, c + ic, opp)
            for bit, (ir, ic, opp) in DIRS.items() if (
                0 <= r + ir < ht and
                0 <= c + ic < wd and
                maze.map[r + ir][c + ic] != 0b10000 and
                (r + ir, c + ic) not in done
            )
        ]
        if neighbors:
            bit, nr, nc, opp = random.choice(neighbors)
            # we change the values of the cells (r,c) and (nr,nc)
            # because we removed a wall in-between
            maze.map[r][c] &= ~bit
            maze.map[nr][nc] &= ~opp
            done.add((nr, nc))
            stack.append((nr, nc))

            # coloring previous cell 
            paint_cell(maze, r, c, Pixel(TRAIL, maze.map[r][c])) 
            # coloring wall 
            paint_cell(maze, nr, nc, Pixel(HEAD, maze.map[nr][nc]))
            # new head of the stack
            paint_wall(
                maze, (r, c), (nr, nc), Pixel(TRAIL, maze.map[r][c])
            )
        else:
            stack.pop() # backtrack
            # this becomes background color
            paint_cell(maze, r, c, Pixel(BG, maze.map[r][c])) 
            if stack:
                top = stack[-1]
                # erase the passage back to it
                paint_wall(
                    maze, (r, c), top, Pixel(BG, maze.map[r][c])
                )
                # head moves back
                paint_cell(maze, *top, Pixel(HEAD, maze.map[top[0]][top[1]]))
        time.sleep(delay)

    if not maze.config.perfect:
        remove_dead_ends(maze, delay)

    start = maze.config.entry
    end = maze.config.exit
    paint_cell(maze, *start, Pixel(START, maze.map[start[0]][start[1]]))
    paint_cell(maze, *end, Pixel(END, maze.map[end[0]][end[1]]))