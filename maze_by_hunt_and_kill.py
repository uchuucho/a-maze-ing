from maze_config_creation import Maze, Pixel
from utils import paint_wall, paint_cell, remove_dead_ends
import random
import time


def hunt_and_kill_generator(
        maze: Maze,
        bg: tuple[int, int, int],
        trail: tuple[int, int, int],
        ss: tuple[int, int, int],
        ee: tuple[int, int, int],
        dirs: dict[int, tuple[int, int, int]],
        delay: float = 0.08
) -> None:

    random.seed(maze.config.seed)

    wd = maze.config.width
    ht = maze.config.height

    # first open cell as the start
    start = (0, 0)
    visited: set[tuple[int, int]] = {start}
    r, c = start
    paint_cell(maze, r, c, Pixel(trail, '*'))
    time.sleep(delay)

    while True:
        # KILL phase
        neighbors = [
            (bit, r + ir, c + ic, opp)
            for bit, (ir, ic, opp) in dirs.items() if (
                0 <= r + ir < ht and 0 <= c + ic < wd and
                (r + ir, c + ic) not in visited and
                maze.map[r+ir][c+ic] != 0b10000
            )
        ]
        if neighbors:
            bit, nr, nc, opp = random.choice(neighbors)
            maze.map[r][c] &= ~bit
            maze.map[nr][nc] &= ~opp
            paint_cell(maze, r, c, Pixel(bg, '*'))
            paint_cell(maze, nr, nc, Pixel(bg, '*'))
            paint_wall(maze, (r, c), (nr, nc), Pixel(bg, '*'))
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
                    for bit, (ir, ic, opp) in dirs.items()
                    if (hr + ir, hc + ic) in visited
                ]
                if vis_nbrs:
                    bit, vr, vc, opp = random.choice(vis_nbrs)
                    maze.map[hr][hc] &= ~bit
                    maze.map[vr][vc] &= ~opp
                    paint_cell(maze, hr, hc, Pixel(bg, '*'))
                    paint_cell(maze, vr, vc, Pixel(bg, '*'))
                    paint_wall(maze, (hr, hc), (vr, vc), Pixel(bg, '*'))
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
        remove_dead_ends(maze, bg, dirs, delay)

    start = maze.config.entry
    end = maze.config.exit
    paint_cell(maze, *start, Pixel(ss, 'S'))
    paint_cell(maze, *end, Pixel(ee, 'E'))
