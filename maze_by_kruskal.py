from maze_config_creation import Maze, Pixel, Theme
from utils import paint_wall, paint_cell, remove_dead_ends
import random
import time


def find_root(
        a: tuple[int, int],
        root: dict[tuple[int, int], tuple[int, int]]
) -> tuple[int, int]:
    x = a
    while x != root[x]:
        x = root[x]
    return x


def unit_roots(
        a: tuple[int, int],
        b: tuple[int, int],
        root: dict[tuple[int, int], tuple[int, int]]
) -> None:
    x, y = find_root(a, root), find_root(b, root)
    root[x] = y


def kruskal_generator(maze: Maze, th: Theme, delay: float = 0.08) -> None:

    random.seed(maze.config.seed)

    wd = maze.config.width
    ht = maze.config.height

    edges_list: list[tuple[tuple[int, int], tuple[int, int]]] = []
    root: dict[tuple[int, int], tuple[int, int]] = {}
    chosen: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for r in range(ht):
        for c in range(wd):
            root[(r, c)] = (r, c)
            for bit, (ir, ic, opp) in th.dirs.items():
                if (
                    0 <= r + ir < ht and 0 <= c + ic < wd and
                    maze.map[r][c] != 0b10000 and
                    maze.map[r + ir][c + ic] != 0b10000
                ):
                    edges_list.append(((r, c), (r + ir, c + ic)))

    random.shuffle(edges_list)

    while edges_list:
        a, b = edges_list.pop()

        if find_root(a, root) != find_root(b, root):
            chosen.append((a, b))
            unit_roots(a, b, root)
            paint_cell(maze, a[0], a[1], Pixel(th.trail, '*'))
            paint_cell(maze, b[0], b[1], Pixel(th.trail, '*'))
            paint_wall(maze, a, b, Pixel(th.trail, '*'))

    for i in range(len(chosen)):
        a, b = chosen[i]
        for bit in th.dirs.keys():
            if (
                th.dirs[bit][0] == b[0] - a[0] and
                th.dirs[bit][1] == b[1] - a[1]
            ):
                maze.map[a[0]][a[1]] &= ~bit
                maze.map[b[0]][b[1]] &= ~th.dirs[bit][2]
                paint_cell(maze, a[0], a[1], Pixel(th.bg, '*'))
                paint_cell(maze, b[0], b[1], Pixel(th.bg, '*'))
                paint_wall(maze, a, b, Pixel(th.bg, '*'))
                time.sleep(delay)
                break

    if not maze.config.perfect:
        remove_dead_ends(maze, th.bg, th.dirs, delay)

    start = maze.config.entry
    end = maze.config.exit
    paint_cell(maze, *start, Pixel(th.start, 'S'))
    paint_cell(maze, *end, Pixel(th.end, 'E'))
