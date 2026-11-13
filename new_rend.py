import random, sys, time


N = 20           # maze is N x N cells
CELL = 4         # interior size in pixels (1:3 ratio with 1px walls)
STEP = CELL + 1  # cell + one wall pixel
SIZE = N * STEP + 1
C = CELL // 2 + 1   # offset of the cell's center pixel from its wall line

BG    = (10, 50, 60)# (30, 22, 15)
WALL  = (224, 163, 78)
PATH  = (255, 240, 200)
START = (200, 120, 220)
END   = (230, 110, 120)
TRAIL = (120, 80, 40)      # cells/passages on the current DFS stack
HEAD1  = (255, 240, 200)    # the cell DFS is standing on
FRONTIER = (120, 80, 40)    # in the stack, waiting
HEAD     = (255, 240, 200)  # just popped




def generate(n):
    visited, stack = {(0, 0)}, [(0, 0)]
    adj = {(x, y): [] for x in range(n) for y in range(n)}
    while stack:
        x, y = stack[-1]
        nbrs = [(x+dx, y+dy) for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))
                if 0 <= x+dx < n and 0 <= y+dy < n and (x+dx, y+dy) not in visited]
        if nbrs:
            nxt = random.choice(nbrs)
            adj[(x, y)].append(nxt); adj[nxt].append((x, y))
            visited.add(nxt); stack.append(nxt)
        else:
            stack.pop()
    return adj

def solve1(adj, start, goal):
    parent, queue = {start: None}, [start]
    for cur in queue:
        if cur == goal:
            break
        for nb in adj[cur]:
            if nb not in parent:
                parent[nb] = cur
                queue.append(nb)
    path, cur = [], goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    return path[::-1]

def fill(img, x0, y0, x1, y1, color):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            img[y][x] = color

def build(n, adj, path):
    img = [[BG] * SIZE for _ in range(SIZE + (SIZE % 2))]   # even height
    # closed grid: every wall is a 1-pixel line
    for i in range(n + 1):
        fill(img, 0, i * STEP, SIZE - 1, i * STEP, WALL)
        fill(img, i * STEP, 0, i * STEP, SIZE - 1, WALL)
    # carve passages
    for a, nbs in adj.items():
        for b in nbs:
            if a < b:
                (x1, y1), (x2, y2) = a, b
                if x1 != x2:
                    fill(img, x2*STEP, y1*STEP+1, x2*STEP, y1*STEP+CELL, BG)
                else:
                    fill(img, x1*STEP+1, y2*STEP, x1*STEP+CELL, y2*STEP, BG)
    # entrance / exit openings
    #fill(img, 1, 0, CELL, 0, BG)
    #fill(img, (n-1)*STEP+1, n*STEP, (n-1)*STEP+CELL, n*STEP, BG)
    # path: 1-pixel line through cell centres, extended through the openings
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        fill(img, min(ax, bx)*STEP + C, min(ay, by)*STEP + C,
                  max(ax, bx)*STEP + C, max(ay, by)*STEP + C, PATH)
    sx, sy = path[0]; ex, ey = path[-1]
    #fill(img, sx*STEP + C, 0, sx*STEP + C, sy*STEP + C, PATH)         # entrance
    #fill(img, ex*STEP + C, ey*STEP + C, ex*STEP + C, n*STEP, PATH)    # exit
    # start / end markers (1 pixel, centre of the cell)
    img[sy*STEP + C][sx*STEP + C] = START
    img[ey*STEP + C][ex*STEP + C] = END
    return img

def render(img):
    out = []
    last = len(img) - 1
    for y in range(0, len(img), 2):
        line = ""
        for x in range(len(img[0])):
            r1, g1, b1 = img[y][x]
            if y + 1 == last and SIZE % 2 == 1:      # padding row
                line += f"\x1b[38;2;{r1};{g1};{b1}m\x1b[49m▀"
            else:
                r2, g2, b2 = img[y+1][x]
                line += f"\x1b[38;2;{r1};{g1};{b1}m\x1b[48;2;{r2};{g2};{b2}m▀"
        out.append(line + "\x1b[0m")
    return "\n".join(out)


def draw_char(img, x, y):
    """Redraw only the character that contains pixel (x, y)."""
    row = y // 2
    r1, g1, b1 = img[row*2][x]        # upper pixel -> foreground
    r2, g2, b2 = img[row*2 + 1][x]    # lower pixel -> background
    sys.stdout.write(f"\x1b[{row+1};{x+1}H"
                     f"\x1b[38;2;{r1};{g1};{b1}m\x1b[48;2;{r2};{g2};{b2}m▀\x1b[0m")

def paint(img, x0, y0, x1, y1, color):
    """Set a rectangle in memory, then redraw only the characters it touches."""
    fill(img, x0, y0, x1, y1, color)
    for row in range(y0 // 2, y1 // 2 + 1):
        for x in range(x0, x1 + 1):
            draw_char(img, x, row * 2)
    sys.stdout.flush()

def interior(c):
    cx, cy = c
    return (cx*STEP + 1, cy*STEP + 1, cx*STEP + CELL, cy*STEP + CELL)

def piece(a, b):
    """The wall piece between neighbouring cells a and b (same rectangle as carving)."""
    (x1, y1), (x2, y2) = sorted((a, b))
    if x1 != x2:   # side by side -> vertical piece
        return (x2*STEP, y1*STEP + 1, x2*STEP, y1*STEP + CELL)
    else:          # one above the other -> horizontal piece
        return (x1*STEP + 1, y2*STEP, x1*STEP + CELL, y2*STEP)

# ---------- closed grid ----------
def build_closed(n):
    img = [[BG] * SIZE for _ in range(SIZE + (SIZE % 2))]
    for i in range(n + 1):
        fill(img, 0, i * STEP, SIZE - 1, i * STEP, WALL)
        fill(img, i * STEP, 0, i * STEP, SIZE - 1, WALL)
    return img

# ---------- DFS with animation ----------
def generate_animated1(n, img, delay=0.03):
    visited = {(0, 0)}
    stack = [(0, 0)]
    adj = {(x, y): [] for x in range(n) for y in range(n)}
    paint(img, *interior((0, 0)), HEAD)
    time.sleep(delay)

    while stack:
        cur = stack[-1]
        x, y = cur
        nbrs = [(x+dx, y+dy) for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))
                if 0 <= x+dx < n and 0 <= y+dy < n and (x+dx, y+dy) not in visited]
        if nbrs:
            nxt = random.choice(nbrs)
            adj[cur].append(nxt); adj[nxt].append(cur)
            visited.add(nxt)
            stack.append(nxt)
            paint(img, *interior(cur), TRAIL)      # old head becomes trail
            paint(img, *piece(cur, nxt), TRAIL)    # open the wall between them
            paint(img, *interior(nxt), HEAD)       # new head
        else:
            stack.pop()                            # backtrack
            paint(img, *interior(cur), BG)         # erase this cell from the snake
            if stack:
                top = stack[-1]
                paint(img, *piece(cur, top), BG)   # erase the passage back to it
                paint(img, *interior(top), HEAD)   # head moves back
        time.sleep(delay)
    return adj


#generating DFS

def generate_animated(n, img, delay=0.03):
    visited = set()
    adj = {(x, y): [] for x in range(n) for y in range(n)}
    stack = [((0, 0), None)]            # (cell, parent)
    last = None                         # previous head

    while stack:
        cell, parent = stack.pop()      # last in, first out
        if cell in visited:
            continue                    # a duplicate entry, ignore it
        visited.add(cell)

        if parent is not None:
            adj[cell].append(parent); adj[parent].append(cell)
            paint(img, *piece(parent, cell), BG)    # open the wall between them
        if last is not None:
            paint(img, *interior(last), BG)         # old head is now a corridor
        paint(img, *interior(cell), HEAD)           # new head
        last = cell

        x, y = cell
        nbrs = [(x+dx, y+dy) for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))
                if 0 <= x+dx < n and 0 <= y+dy < n and (x+dx, y+dy) not in visited]
        random.shuffle(nbrs)
        for nb in nbrs:
            stack.append((nb, cell))
            paint(img, *interior(nb), FRONTIER)     # show it waiting
        time.sleep(delay)

    paint(img, *interior(last), BG)                 # last head becomes a corridor
    return adj

#generating shortest path

def solve(adj, start, goal):
    """BFS: shortest path as a list of cells."""
    parent, queue = {start: None}, [start]
    for cur in queue:
        if cur == goal:
            break
        for nb in adj[cur]:
            if nb not in parent:
                parent[nb] = cur
                queue.append(nb)
    path, cur = [], goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    return path[::-1]

def path_pixels(path):
    """Ordered list of pixels, from the centre of the start cell to the centre of the end cell."""
    x, y = path[0][0]*STEP + C, path[0][1]*STEP + C
    pts = [(x, y)]
    for cx, cy in path[1:]:
        tx, ty = cx*STEP + C, cy*STEP + C
        while (x, y) != (tx, ty):                 # one pixel per step
            x += (tx > x) - (tx < x)
            y += (ty > y) - (ty < y)
            pts.append((x, y))
    return pts

def set_pixel(img, x, y, color):
    img[y][x] = color        # update memory
    draw_char(img, x, y)     # redraw the one character that holds this pixel
    sys.stdout.flush()


#explosion

import math

# explosion colors, from first frame to last (white-hot -> dark red)
EXPLOSION = [(255, 255, 255), (255, 240, 160), (255, 200, 60),
             (255, 140, 30), (220, 60, 20), (120, 30, 15)]

def explode(img, cx, cy, frames=120, particles=1045, delay=0.04):
    ox, oy = cx*STEP + C, cy*STEP + C          # centre pixel of the end cell

    # flash: the whole end cell goes white for a moment
    paint(img, *interior((cx, cy)), (255, 255, 255))
    time.sleep(0.1)

    # each particle gets a random direction and speed (pixels per frame)
    parts = []
    for _ in range(particles):
        ang = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.6, 2.2)
        parts.append((math.cos(ang) * speed, math.sin(ang) * speed))

    shown = {}                                  # pixel -> its original color
    for t in range(frames):
        # 1. put back what the previous frame covered
        for (x, y), original in shown.items():
            set_pixel(img, x, y, original)
        shown = {}

        # 2. colour for this frame: moves along the EXPLOSION list over time
        color = EXPLOSION[t * len(EXPLOSION) // frames]

        # 3. draw every particle at its new position
        for vx, vy in parts:
            x = round(ox + vx * t)
            y = round(oy + vy * t)
            if 0 <= x < SIZE and 0 <= y < SIZE and (x, y) not in shown:
                shown[(x, y)] = img[y][x]       # remember the original
                set_pixel(img, x, y, color)
        time.sleep(delay)

    # clean up the last frame
    for (x, y), original in shown.items():
        set_pixel(img, x, y, original)

    # the target is destroyed: its cell becomes an empty corridor
    paint(img, *interior((cx, cy)), BG)


#main

if __name__ == "__main__":
    img = build_closed(N)
    sys.stdout.write("\x1b[2J\x1b[H\x1b[?25l")
    try:
        sys.stdout.write(render(img))
        sys.stdout.flush()
        """
        # 1. animated maze generation
        adj = generate_animated(N, img, delay=0.03)

        # 2. shortest path
        start, goal = (0, 0), (N - 1, N - 1)
        path = solve(adj, start, goal)

        # 3. animated path, one pixel at a time
        for x, y in path_pixels(path):
            set_pixel(img, x, y, PATH)
            time.sleep(0.02)

        # 4. start and end markers on top
        set_pixel(img, start[0]*STEP + C, start[1]*STEP + C, START)
        set_pixel(img, goal[0]*STEP + C, goal[1]*STEP + C, END)
        time.sleep(0.3)

        # 5. explosion at the end cell
        explode(img, goal[0], goal[1])
        """
    finally:
        sys.stdout.write(f"\x1b[{len(img)//2 + 1};1H\x1b[?25h\n")
    s = input("Enough?")

"""
if __name__ == "__main__":
    img = build_closed(N)
    sys.stdout.write("\x1b[2J\x1b[H\x1b[?25l")
    try:
        sys.stdout.write(render(img))              # closed grid, drawn once
        sys.stdout.flush()
        adj = generate_animated(N, img, delay=0.05)
    finally:
        sys.stdout.write(f"\x1b[{len(img)//2 + 1};1H\x1b[?25h\n")
"""