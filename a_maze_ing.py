from maze_config_creation import MazeConfig, ConfigError, Maze, Pixel
from maze_by_dfs import dfs_generate
from utils import print_path, explode
import sys
import time


BG    = (10, 50, 60)        # cell background
PATH  = (255, 240, 200)     # shortest path
START = (235, 7, 7)     # entry 
END   = (15, 28, 209)     # exit
WALL = (224, 163, 78)       # wall
S42 = (52, 55, 235)



def rendering(maze: Maze) -> str:
    out: list[str] = []

    step = maze.config.cell + 1
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

def rend(maze: Maze) -> str:
    out: list[str] = []

    step = maze.config.cell + 1
    height = len(maze.pixels)
    width = len(maze.pixels[0])
    for y in range(0, height):
        line = ""
        for x in range(width):
            r1, g1, b1 = maze.pixels[y][x].color
            line += f"\x1b[38;2;{r1};{g1};{b1}m\x1b[49m▀"
        out.append(line + "\x1b[0m")
    return "\n".join(out)


def park(maze: Maze, l: int = 0) -> None:
    rows = (len(maze.pixels) + 1) // 2
    sys.stdout.write(f"\x1b[{rows + 1 + l};1H\x1b[J")   # go below the maze, clear what is under it
    sys.stdout.flush()


def agenda() -> None:
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
    sys.stdout.flush()



if __name__ == "__main__":
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
    maze.pixel_init()
    # maze.__print_maze_map__()
    # maze.__print_maze_pixel__()
    
    
    # preparing printing maze

    # raw maze: clean screen
    sys.stdout.write(
        "\x1b[2J"       #delete entire screen
        "\x1b[H"        #bring cursor to the home 1x1 pixel
        "\x1b[?25l"     #hide the cursor
    )
    sys.stdout.write(rendering(maze))
    sys.stdout.flush()

    dfs_generate(maze, 0.08)

    sys.stdout.write(f"\x1b[{len(maze.pixels)//2 + 1};1H\x1b[?25h\n")

    park(maze)
    agenda()
    n = 0
    while True:
        print()
        print("\nPress Enter to exit the program")
        print("\nPress P to print/hide the shortest path")
        s = input("\n")
        if len(s) == 0:
            break
        if s == 'P' or s == 'p':
            n += 1
            if n % 2 == 1:
                print_path(maze, Pixel(PATH, 0b0000), 0.08)
                explode(maze, maze.config.exit, 100, 600, 0.04)
            else:
                print_path(maze, Pixel(BG, 0b0000), 0.00)
        park(maze, 7)
            