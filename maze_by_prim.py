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



def prim_generator(maze: Maze, delay: float = 0.03):
    random.seed(maze.config.seed)
    
    start = maze.config.entry
    end = maze.config.exit
    wd = maze.config.width
    ht = maze.config.height
    
    done: set[tuple[int, int]] = set()
    front: set[tuple[int, int]] = {start}
    adj: list[tuple[int, int]] = [start]

    while adj:
        i = random.randrange(len(adj))
        adj[i], adj[-1] = adj[-1], adj[i]

        r, c = adj.pop()
        front.discard((r, c))
        done.add((r, c))
        paint_cell(maze, r, c, Pixel(BG, maze.map[r][c]))
        
        ins: list[tuple[int, int, int, int]] = []
        for bit, (ir, ic, opp) in DIRS.items():
            nr, nc = r + ir, c + ic
            if not (0 <= nr < ht and 0 <= nc < wd):
                continue
            if maze.map[nr][nc] == 0b10000:
                continue
            if (nr, nc) in done:
                ins.append((bit, nr, nc, opp))
            elif (nr, nc) not in front:
                front.add((nr, nc))
                adj.append((nr, nc))
                paint_cell(maze, nr, nc, Pixel(TRAIL, maze.map[nr][nc]))
                
        if ins:
            bit, nr, nc, opp = random.choice(ins)
            maze.map[r][c] &= ~bit
            maze.map[nr][nc] &= ~opp
            paint_wall(maze, (r, c), (nr, nc), Pixel(BG, maze.map[r][c]))

        time.sleep(delay)

    if not maze.config.perfect:
        remove_dead_ends(maze, delay)

    paint_cell(maze, *start, Pixel(START, maze.map[start[0]][start[1]]))
    paint_cell(maze, *end, Pixel(END, maze.map[end[0]][end[1]]))


