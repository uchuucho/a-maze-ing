from maze_config_creation import Maze, Pixel, Theme
from utils import paint_wall, paint_cell, remove_dead_ends
import random
import time


def hunt_and_kill_generator(
        maze: Maze, th: Theme, delay: float = 0.08
) -> None:

    random.seed(maze.config.seed)

    wd = maze.config.width
    ht = maze.config.height

    # first open cell as the start
    start = (0, 0)
    visited: set[tuple[int, int]] = {start}
    r, c = start
    paint_cell(maze, r, c, Pixel(th.trail, '*'))
    time.sleep(delay)

    while True:
        # KILL phase
        neighbors = [
            (bit, r + ir, c + ic, opp)
            for bit, (ir, ic, opp) in th.dirs.items() if (
                0 <= r + ir < ht and 0 <= c + ic < wd and
                (r + ir, c + ic) not in visited and
                maze.map[r+ir][c+ic] != 0b10000
            )
        ]
        if neighbors:
            bit, nr, nc, opp = random.choice(neighbors)
            maze.map[r][c] &= ~bit
            maze.map[nr][nc] &= ~opp
            paint_cell(maze, r, c, Pixel(th.bg, '*'))
            paint_cell(maze, nr, nc, Pixel(th.bg, '*'))
            paint_wall(maze, (r, c), (nr, nc), Pixel(th.bg, '*'))
            time.sleep(delay)

            visited.add((nr, nc))
            r, c = nr, nc
            continue

        # HUNT phase
        found = False
        for hr in range(ht):
            for hc in range(wd):
                if maze.map[hr][hc] == 0b10000 or (hr, hc) in visited:
                    continue
                # visited neighbors of this unvisited cell
                vis_nbrs = [
                    (bit, hr + ir, hc + ic, opp)
                    for bit, (ir, ic, opp) in th.dirs.items()
                    if (hr + ir, hc + ic) in visited
                ]
                if vis_nbrs:
                    bit, vr, vc, opp = random.choice(vis_nbrs)
                    maze.map[hr][hc] &= ~bit
                    maze.map[vr][vc] &= ~opp
                    paint_cell(maze, hr, hc, Pixel(th.bg, '*'))
                    paint_cell(maze, vr, vc, Pixel(th.bg, '*'))
                    paint_wall(maze, (hr, hc), (vr, vc), Pixel(th.bg, '*'))
                    time.sleep(delay)

                    visited.add((hr, hc))
                    r, c = hr, hc
                    found = True
                    break
            if found:
                break
        if not found:
            break

    if not maze.config.perfect:
        remove_dead_ends(maze, th.bg, th.dirs, delay)

    start = maze.config.entry
    end = maze.config.exit
    paint_cell(maze, *start, Pixel(th.start, 'S'))
    paint_cell(maze, *end, Pixel(th.end, 'E'))
