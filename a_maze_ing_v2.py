from maze_config_creation import MazeConfig, ConfigError, Maze, Pixel
from mazegen import MazeGenerator
from mazegen.generator import DIRS
from utils import paint_cell, paint_wall, print_path, explode
import sys
import time


# colors
BG = (10, 50, 60)        # cell background
WALL = (224, 163, 78)     # wall
HEAD = (98, 252, 3)     # the cell DFS is standing on
PATH = (255, 240, 200)    # shortest path
START = (235, 7, 7)     # entry
END = (10, 140, 12)     # exit
S42 = (52, 55, 235)
WALL_COLORS = [WALL, (200, 200, 200), (120, 180, 255), (255, 120, 160)]
FORTY_TWO = 0b10000  # marks a '42' cell (walls use 0-15)
DELAY = 0.03  # seconds between animation frames

def rendering(maze: Maze) -> str:
    out: list[str] = []

    height = len(maze.pixels)
    width = len(maze.pixels[0])
    for y in range(0, height, 2):
        line = ""
        for x in range(width):
            r1, g1, b1 = maze.pixels[y][x].color
            if y + 1 >= height:
                line += f"\x1b[38;2;{r1};{g1};{b1}m\x1b[49m▀"
            else:
                r2, g2, b2 = maze.pixels[y+1][x].color
                line += f"\x1b[38;2;{r1};{g1};{b1}m"
                line += f"\x1b[48;2;{r2};{g2};{b2}m▀"
        out.append(line + "\x1b[0m")
    return "\n".join(out)


# locating maze
# go below the maze, clear what is under it
def park(maze: Maze, ll: int = 0) -> None:
    rows = (len(maze.pixels) + 1) // 2
    sys.stdout.write(f"\x1b[{rows + 1 + ll};1H\x1b[J")
    sys.stdout.flush()


# explanation what are what
def agenda(maze: Maze) -> None:
    colors: list[tuple[tuple[int, int, int], str]] = [
        (BG, "maze cell"),
        (WALL, "wall"),
        (START, "entry cell"),
        (END, "exit cell"),
        (PATH, "path between entry and exit"),
        (S42, "42 symbol")
    ]
    sys.stdout.write("\n")
    for color, key in colors:
        r, g, b = color
        sys.stdout.write(f"\r{f"\x1b[48;2;{r};{g};{b}m \x1b[0m"} {key}")
        sys.stdout.write("\n")
    sys.stdout.write(f"Algorithm: {maze.config.algorithm}\n")
    sys.stdout.flush()


# printing maze
def main(maze: Maze) -> None:

    # raw maze: clean screen
    sys.stdout.write(
        "\x1b[2J"       # delete entire screen
        "\x1b[H"        # bring cursor to the home 1x1 pixel
        "\x1b[?25l"     # hide the cursor
    )
    sys.stdout.write(rendering(maze))
    sys.stdout.flush()

    # algorithm
    if maze.config.algorithm == 'dfs':
        dfs_generator(maze, BG, HEAD, TRAIL, START, END, DIRS, 0.08)
    elif maze.config.algorithm == 'prim':
        prim_generator(maze, BG, TRAIL, START, END, DIRS, 0.08)
    elif maze.config.algorithm == 'kruskal':
        kruskal_generator(maze, BG, TRAIL, START, END, DIRS, 0.08)
    elif maze.config.algorithm == 'hunt_and_kill':
        hunt_and_kill_generator(maze, BG, TRAIL, START, END, DIRS, 0.1)
    else:
        raise ConfigError("Unknown algorithm")

    sys.stdout.write(f"\x1b[{len(maze.pixels)//2 + 1};1H\x1b[?25h\n")

    park(maze)
    agenda(maze)
    n = 0
    while True:
        print()
        print("\nPress [Enter] to exit the program")
        print("Press [P] or [p] to print the shortest path")
        print("Press [H] or [h] to hide the shortest path")
        print("Press [B] or [b] to print the maze blueprint")
        print("Press [F] or [f] to save the maze map to a file\n")

        s = input("Your choice: ")
        if len(s) == 0:
            break
        if n == 0 and (s == 'P' or s == 'p'):
            n += 1
            print_path(maze, Pixel(PATH, 'x'), START, END, DIRS, 0.08)
            explode(maze, maze.config.exit, BG, 100, 600, 0.04)
        if n == 1 and (s == 'H' or s == 'h'):
            n -= 1
            print_path(maze, Pixel(BG, '*'), START, END, DIRS, 0.00)
        if s == 'B' or s == 'b':
            maze.__print_maze_pixel__()
            break
        if s == 'F' or s == 'f':
            maze.__save_maze_map__(
                print_path(maze, Pixel(PATH, 'x'), START, END, DIRS, 0.08, 1)
            )
            break

        park(maze, 8)


if __name__ == "__main__":
    bg = Pixel(BG, '*')
    wall = Pixel(WALL, '#')
    s42 = Pixel(S42, 'o')

    print(sys.argv)
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt")
        sys.exit(1)

    try:
        cfg = MazeConfig.create_maze_config(sys.argv[1])
        print(cfg)
    except ConfigError as e:
        print(e)
        sys.exit(1)

    print("=======================")
    maze = Maze(cfg)
    maze.add42()
    maze.pixel_update(wall, bg, s42)

    try:
        main(maze)
    except Exception as e:
        print(e)
