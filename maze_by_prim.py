from maze_config_creation import Maze, Pixel, Theme
from utils import paint_wall, paint_cell, remove_dead_ends
import random
import time


def prim_generator(maze: Maze, th: Theme, delay: float = 0.03) -> None:

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
        paint_cell(maze, r, c, Pixel(th.bg, '*'))

        ins: list[tuple[int, int, int, int]] = []
        for bit, (ir, ic, opp) in th.dirs.items():
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
                paint_cell(maze, nr, nc, Pixel(th.trail, '*'))

        if ins:
            bit, nr, nc, opp = random.choice(ins)
            maze.map[r][c] &= ~bit
            maze.map[nr][nc] &= ~opp
            paint_wall(maze, (r, c), (nr, nc), Pixel(th.bg, '*'))

        time.sleep(delay)

    if not maze.config.perfect:
        remove_dead_ends(maze, th.bg, th.dirs, delay)

    paint_cell(maze, *start, Pixel(th.start, 'S'))
    paint_cell(maze, *end, Pixel(th.end, 'E'))
