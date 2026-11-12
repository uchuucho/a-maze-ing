from maze_config_creation import Maze, MazeConfig, Pixel
import random
import sys
import time
import math



# binary location: 0bWSEN -> 1 wall 0 no wall
N, E, S, W = 1, 2, 4, 8
# directions: (row, col, opposite_dir)
DIRS = {N: (-1, 0, S), E: (0, 1, W), S: (1, 0, N), W: (0, -1, E)}

# colors
BG    = (10, 50, 60)        # cell background
WALL = (224, 163, 78)       # wall
FRONTIER = (186, 252, 3)        # cells/passages on the current DFS stack
HEAD  = (98, 252, 3)     # the cell DFS is standing on
TRAIL = (120, 80, 40)    # in the stack, waiting

PATH  = (255, 240, 200)     # shortest path
START = (235, 7, 7)     # entry 
END   = (15, 28, 209)     # exit

# explosion colors, from first frame to last (white-hot -> dark red)
EXPLOSION = [(255, 255, 255), (255, 240, 160), (255, 200, 60),
             (255, 140, 30), (220, 60, 20), (120, 30, 15)]


def paint_cell(maze: Maze, r: int, c: int, pix: Pixel) -> None:
    cell = maze.config.cell
    step = cell + 1
    i0, i1 = step * r + 1, step * r + cell
    j0, j1 = step * c + 1, step * c + cell
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            maze.pixels[i][j] = pix
    
    for ty in range(i0 // 2, i1 // 2 + 1):
        y = 2 * ty
        sys.stdout.write(f"\x1b[{ty + 1};{j0 + 1}H")
        for j in range(j0, j1 + 1):
            r1, g1, b1 = maze.pixels[y][j].color
            r2, g2, b2 = maze.pixels[y + 1][j].color
            sys.stdout.write(
                f"\x1b[38;2;{r1};{g1};{b1}m"
                f"\x1b[48;2;{r2};{g2};{b2}m▀"
            )
        sys.stdout.write("\x1b[0m")
    sys.stdout.flush()


def paint_wall(
        maze: Maze,
        aa: tuple[int, int],
        bb: tuple[int, int],
        pix: Pixel
) -> None:
    cell = maze.config.cell
    step = cell + 1

    if aa[0] == bb[0]: #same row, vertical wall
        r = aa[0]
        j = step * max(aa[1], bb[1])
        i0, i1 = step * r + 1, step * r + cell
        j0, j1 = j, j
        for i in range(i0, i1 + 1):
            maze.pixels[i][j] = pix
    else:
        c = aa[1]
        i = step * max(aa[0], bb[0])
        i0, i1 = i, i
        j0, j1 = step * c + 1, step * c + cell
        for j in range(j0, j1 + 1):
            maze.pixels[i][j] = pix

    for ty in range(i0 // 2, i1 // 2 + 1):
        y = 2 * ty
        sys.stdout.write(f"\x1b[{ty + 1};{j0+1}H")
        for j in range(j0, j1 + 1):
            r1, g1, b1 = maze.pixels[y][j].color
            r2, g2, b2 = maze.pixels[y + 1][j].color
            sys.stdout.write(
                f"\x1b[38;2;{r1};{g1};{b1}m"
                f"\x1b[48;2;{r2};{g2};{b2}m▀"
            )
        sys.stdout.write("\x1b[0m")
    sys.stdout.flush()


def paint_line(
        maze: Maze,
        aa: tuple[int, int],
        bb: tuple[int, int],
        pix: Pixel
) -> None:
    
    step = maze.config.cell + 1
    mid = maze.config.cell // 2 + 1
    
    i0 = step * min(aa[0], bb[0]) + mid
    i1 = step * max(aa[0], bb[0]) + mid
    j0 = step * min(aa[1], bb[1]) + mid
    j1 = step * max(aa[1], bb[1]) + mid
    
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            maze.pixels[i][j] = pix
    
    for ty in range(i0 // 2, i1 // 2 + 1):
        y = 2 * ty
        sys.stdout.write(f"\x1b[{ty + 1};{j0+1}H")
        for j in range(j0, j1 + 1):
            r1, g1, b1 = maze.pixels[y][j].color
            r2, g2, b2 = maze.pixels[y + 1][j].color
            sys.stdout.write(
                f"\x1b[38;2;{r1};{g1};{b1}m"
                f"\x1b[48;2;{r2};{g2};{b2}m▀"
            )
        sys.stdout.write("\x1b[0m")
    sys.stdout.flush()



def remove_dead_ends(maze: Maze, delay: float = 0.03) -> None:
    cell = maze.config.cell

    for r in range(maze.config.height):
        for c in range(maze.config.width):
            if maze.map[r][c] not in [7, 11, 13, 14]:
                continue
            # choose all wall sides
            blocks = [
                (bit, r + ir, c + ic, opp)
                for bit, (ir, ic, opp) in DIRS.items() if (
                        maze.map[r][c] & bit and
                        0 <= r + ir < maze.config.height and
                        0 <= c + ic < maze.config.width and
                        maze.map[r + ir][c + ic] != 0b10000
                    )
            ]
            if not blocks:
                continue
            # check maybe a neighbor is also dead-end
            # so we open just one wall
            twins = [
                x for x in blocks
                if maze.map[x[1]][x[2]] in [7, 11, 13, 14]
            ]
            bit, nr, nc, opp = random.choice(twins or blocks)
            maze.map[r][c] &= ~bit
            maze.map[nr][nc] &= ~opp
            paint_wall(
                maze, (r, c), (nr, nc), Pixel(BG, maze.map[r][c])
            )
        time.sleep(delay)


def shortest_path(maze: Maze, delay: float = 0.08) -> list[tuple[int, int]]:

    start, end = maze.config.entry, maze.config.exit
    parent: dict[tuple[int, int], tuple[int, int]] = {start: start}

    queue: list[tuple[int, int]] = [start]
    n = 0
    while n < len(queue) and end not in queue:
        cur = queue[n]
        n += 1
        for cc, (ir, ic, _) in DIRS.items():
            if maze.map[cur[0]][cur[1]] & cc: # wall in direction cc
                continue
            if (cur[0] + ir, cur[1] + ic) in parent:
                continue
            parent[(cur[0] + ir, cur[1] + ic)] = cur
            queue.append((cur[0] + ir, cur[1] + ic))

    if end not in queue:
        return []

    mid = maze.config.cell // 2 + 1
    path: list[tuple[int, int]] = []
    path.append(end)
    cur = end
    while parent[cur] != cur:
        cur = parent[cur]
        path.insert(0, cur)

    return path
    

def print_path(
        maze: Maze,
        pix: Pixel,
        delay: float = 0.03
) -> None:
    path = shortest_path(maze, delay)
    # put shortest path    
    u = path[0]
    for v in path[1: ]:
        paint_line(maze, u, v, pix)
        u = v
        time.sleep(delay)
    paint_cell(maze, *path[0], Pixel(START, maze.map[path[0][0]][path[0][1]]))
    paint_cell(maze, *path[-1], Pixel(END, maze.map[path[-1][0]][path[-1][1]]))



def explode(
    maze: Maze,
    center: tuple[int, int],
    frames: int = 120,
    n_particles: int = 1045,
    delay: float = 0.04,
    destroy: bool = False        # True: the cell becomes an empty BG corridor at the end
) -> None:
    cell = maze.config.cell
    step = cell + 1
    mid = cell // 2 + 1
    ht = step * maze.config.height + 1
    wd = step * maze.config.width + 1
    cr, cx = center[0] * step + mid, center[1] * step + mid   # centre pixel (row, col)

    # interior pixels of the exit cell
    i0, i1 = step * center[0] + 1, step * center[0] + cell
    j0, j1 = step * center[1] + 1, step * center[1] + cell

    def term_cell(top: int, x: int, lit: dict) -> str:
        """Escape sequence for the terminal cell holding pixel rows top, top+1."""
        up = lit.get((top, x), maze.pixels[top][x].color)
        s = f"\x1b[{top // 2 + 1};{x + 1}H\x1b[38;2;{up[0]};{up[1]};{up[2]}m"
        if top + 1 < ht:
            lo = lit.get((top + 1, x), maze.pixels[top + 1][x].color)
            s += f"\x1b[48;2;{lo[0]};{lo[1]};{lo[2]}m"
        else:
            s += "\x1b[49m"
        return s + "▀"

    # 1. save the real pixels of the exit cell
    saved = [[maze.pixels[i][j] for j in range(j0, j1 + 1)]
             for i in range(i0, i1 + 1)]

    # 2. flash
    paint_cell(maze, *center, Pixel((255, 255, 255), maze.map[center[0]][center[1]]))
    time.sleep(0.1)

    # 3. put the real pixels back in the data and redraw the cell on screen
    for di, row in enumerate(saved):
        for dj, pix in enumerate(row):
            maze.pixels[i0 + di][j0 + dj] = pix
    sys.stdout.write("".join(
        term_cell(top, x, {})
        for top in range(2 * (i0 // 2), i1 + 1, 2)
        for x in range(j0, j1 + 1)
    ) + "\x1b[0m")
    sys.stdout.flush()

    # 4. particles: random direction and speed (pixels per frame)
    parts = []
    for _ in range(n_particles):
        ang = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.6, 2.2)
        parts.append((math.cos(ang) * speed, math.sin(ang) * speed))

    prev: set[tuple[int, int]] = set()      # terminal cells drawn in the last frame
    for t in range(frames):
        color = EXPLOSION[t * len(EXPLOSION) // frames]
        lit: dict[tuple[int, int], tuple[int, int, int]] = {}
        for vx, vy in parts:
            x = round(cx + vx * t)
            y = round(cr + vy * t)
            if 0 <= y < ht and 0 <= x < wd:
                lit[(y, x)] = color
        cells = {(2 * (y // 2), x) for (y, x) in lit}

        buf = [term_cell(top, x, {}) for (top, x) in prev - cells]   # restore old
        buf += [term_cell(top, x, lit) for (top, x) in cells]        # draw new
        buf.append("\x1b[0m")
        sys.stdout.write("".join(buf))
        sys.stdout.flush()
        prev = cells
        time.sleep(delay)

    # 5. clean up the last frame (redraws from the restored maze.pixels)
    sys.stdout.write("".join(term_cell(top, x, {}) for (top, x) in prev) + "\x1b[0m")
    sys.stdout.flush()

    # 6. optional: the target is destroyed and becomes an empty corridor
    if destroy:
        paint_cell(maze, *center, Pixel(BG, maze.map[center[0]][center[1]]))