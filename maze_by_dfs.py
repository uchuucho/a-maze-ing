from maze_config_creation import Maze, Pixel
from utils import paint_wall, paint_cell, remove_dead_ends
import random
import time


def dfs_generator(
        maze: Maze,
        bg: tuple[int, int, int],
        head: tuple[int, int, int],
        trail: tuple[int, int, int],
        ss: tuple[int, int, int],
        ee: tuple[int, int, int],
        dirs: dict[int, tuple[int, int, int]],
        delay: float = 0.03
) -> None:

    random.seed(maze.config.seed)

    wd = maze.config.width
    ht = maze.config.height

    done: set[tuple[int, int]] = {maze.config.entry}
    stack: list[tuple[int, int]] = [maze.config.entry]

    paint_cell(maze, *maze.config.entry, Pixel(head, '*'))
    time.sleep(delay)

    while stack:
        r, c = stack[-1]
        neighbors = [
            (bit, r + ir, c + ic, opp)
            for bit, (ir, ic, opp) in dirs.items() if (
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
            paint_cell(maze, r, c, Pixel(trail, '*'))
            # coloring wall
            paint_cell(maze, nr, nc, Pixel(head, '*'))
            # new head of the stack
            paint_wall(
                maze, (r, c), (nr, nc), Pixel(trail, '*')
            )
        else:
            stack.pop()  # backtrack

            # this becomes background color
            paint_cell(maze, r, c, Pixel(bg, '*'))
            if stack:
                top = stack[-1]
                # erase the passage back to it
                paint_wall(
                    maze, (r, c), top, Pixel(bg, '*')
                )
                # head moves back
                paint_cell(maze, *top, Pixel(head, '*'))
        time.sleep(delay)

    if not maze.config.perfect:
        remove_dead_ends(maze, bg, dirs, delay)

    start = maze.config.entry
    end = maze.config.exit
    paint_cell(maze, *start, Pixel(ss, 'S'))
    paint_cell(maze, *end, Pixel(ee, 'E'))
