from maze_config_creation import MazeConfig, ConfigError, Maze, Pixel, Theme
from maze_by_dfs import dfs_generator
from maze_by_prim import prim_generator
from maze_by_kruskal import kruskal_generator
from maze_by_hunt_and_kill import hunt_and_kill_generator
from utils import print_path, explode
from dataclasses import replace
import sys
import random


# binary location: 0bWSEN -> 1 wall 0 no wall
N, E, S, W = 1, 2, 4, 8
# directions: (row, col, opposite_dir)
DIRS = {N: (-1, 0, S), E: (0, 1, W), S: (1, 0, N), W: (0, -1, E)}

# colors
BG = (10, 50, 60)        # cell background
WALL = (224, 163, 78)     # wall
HEAD = (98, 252, 3)     # the cell DFS is standing on
TRAIL = (120, 80, 40)    # in the stack, waiting
PATH = (255, 240, 200)    # shortest path
START = (235, 7, 7)     # entry
END = (10, 140, 12)     # exit
S42 = (52, 55, 235)    # 42 color
WALL_COLORS = [
    (224, 163, 78),   # amber (your current one)
    (232, 93, 117),   # coral rose
    (186, 104, 200),  # orchid purple
    (100, 181, 246),  # sky blue
    (77, 208, 225),   # bright cyan
    (129, 199, 132),  # soft green
    (255, 202, 40),   # golden yellow
    (255, 138, 101),  # peach orange
    (240, 98, 146),   # hot pink
    (176, 190, 197),  # silver grey
]


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
    wall = maze.pixels[0][0].color
    colors: list[tuple[tuple[int, int, int], str]] = [
        (BG, "corridor"),
        (wall, "wall"),
        (START, "entry"),
        (END, "exit"),
        (PATH, "shertest path"),
        (S42, "42 symbol")
    ]
    sys.stdout.write("\n")
    items: list[str] = []
    for color, key in colors:
        r, g, b = color
        cmd = f"\x1b[48;2;{r};{g};{b}m \x1b[0m"
        items.append(f"{cmd}{key}")

    sys.stdout.write("\n\r" + "  ".join(items))
    sys.stdout.write(f"\nAlgorithm: {maze.config.algorithm}\n")
    sys.stdout.flush()


def bottom(maze: Maze, msg: str = "") -> None:
    park(maze)
    agenda(maze)
    print("\nPress [Enter] to exit the program")
    print("Press [P] or [p] to print the shortest path")
    print("Press [H] or [h] to hide the shortest path")
    print("Press [B] or [b] to print the maze blueprint")
    print("Press [F] or [f] to save the maze map to a file")
    print("Press [R] or [r] to generate new map")
    print("Press [C] or [c] to change the wall colors\n")
    if msg:
        print(f"{msg}")
    print()


# building and printing a maze
def build(maze: Maze, delay: float = 0.0) -> None:
    # raw maze: clean screen
    sys.stdout.write(
        "\x1b[2J"       # delete entire screen
        "\x1b[H"        # bring cursor to the home 1x1 pixel
        "\x1b[?25l"     # hide the cursor
    )
    sys.stdout.write(rendering(maze))
    sys.stdout.flush()

    theme = Theme(DIRS, BG, HEAD, TRAIL, START, END)
    # algorithm
    if maze.config.algorithm == 'dfs':
        dfs_generator(maze, theme, delay)
    elif maze.config.algorithm == 'prim':
        prim_generator(maze, theme, delay)
    elif maze.config.algorithm == 'kruskal':
        kruskal_generator(maze, theme, delay)
    elif maze.config.algorithm == 'hunt_and_kill':
        hunt_and_kill_generator(maze, theme, delay)
    else:
        raise ConfigError("Unknown algorithm")

    sys.stdout.write("\x1b[?25h\n")

    park(maze)
    agenda(maze)


# printing maze
def main(maze: Maze) -> None:
    build(maze, 0.08)
    n = 0
    msg = ""
    while True:
        bottom(maze, msg)
        try:
            s = input("Your choice: ").strip().lower()
        except EOFError:
            break

        if not s:
            break
        # printing path
        if s == 'p' and n == 0:
            n = 1
            print_path(maze, Pixel(PATH, 'x'), START, END, DIRS, 0.08)
            explode(maze, maze.config.exit, BG, 100, 600, 0.04)

        # hiding path
        elif s == 'h' and n == 1:
            n = 0
            print_path(maze, Pixel(BG, '*'), START, END, DIRS, 0.00)

        # printing blueprints/pixels
        elif s == 'b':
            # enter alternate screen, cursor home
            sys.stdout.write("\x1b[?1049h\x1b[H")
            sys.stdout.flush()
            try:
                maze.__print_maze_pixel__()
                input("\nPress [Enter] to go back")
            finally:
                # leave to old screen
                sys.stdout.write("\x1b[?1049l")
                sys.stdout.flush()

        # saving maze map to a file
        elif s == 'f':
            try:
                maze.__save_maze_map__(
                    print_path(
                        maze, Pixel(PATH, 'x'), START, END, DIRS, 0.08, 1
                    )
                )
                msg = f"Saved to {maze.config.output_file}"
            except ConfigError as e:
                msg = str(e)

        # regenerate new maze
        elif s == 'r':
            wall = maze.pixels[0][0].color
            try:
                new_cfg = replace(
                    maze.config,
                    seed=random.randint(0, 1000),
                    algorithm=random.choice(
                        ['dfs', 'prim', 'kruskal', 'hunt_and_kill']
                    )
                )
                new_maze = Maze(new_cfg)
                new_maze.add42()
                new_maze.pixel_update(
                    Pixel(wall, '#'), Pixel(BG, '*'), Pixel(S42, 'o')
                )
            except (ConfigError, OSError, ValueError) as e:
                msg = f"Error: {e}"
            else:
                maze = new_maze
                n = 0
                build(maze, 0.08)
                msg = ""

        # recoloring walls
        elif s == 'c':
            old = maze.pixels[0][0].color
            new = random.choice(
                [c for c in WALL_COLORS if c != old]
            )
            new_pix = Pixel(new, '#')
            for row in maze.pixels:
                for j, p in enumerate(row):
                    if p.color == old:
                        row[j] = new_pix
            sys.stdout.write("\x1b7")                      # save cursor
            sys.stdout.write("\x1b[H" + rendering(maze))   # redraw maze
            sys.stdout.write("\x1b8")                      # restore cursor
            sys.stdout.flush()


if __name__ == "__main__":

    print(sys.argv)
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt")
        sys.exit(1)

    try:
        cfg = MazeConfig.create_maze_config(sys.argv[1])
        maze = Maze(cfg)
        maze.add42()
        maze.pixel_update(
            Pixel(WALL, '#'), Pixel(BG, '*'), Pixel(S42, 'o')
        )
    except (ConfigError, OSError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        main(maze)
    except KeyboardInterrupt:
        park(maze)
        print("\nProgram stopped by user")
    except (ConfigError, OSError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        sys.stdout.write("\x1b[0m\x1b[?25h\n")   # reset colors, show cursor
        sys.stdout.flush()
