"""A-Maze-ing: generate a maze from a config file and display it."""
import signal
import sys

from display import WALL_COLORS, Canvas, fit_cell_size, generate, legend
from maze_config_creation import ConfigError, MazeConfig
from mazegen import MazeGenerator

MENU = "[r] regenerate   [p] show/hide path   [c] wall color   [q] quit"
# switch to a separate blank screen and back, so the
# maze never mixes with what was in the terminal before
ALT_SCREEN_ON = "\x1b[?1049h"
ALT_SCREEN_OFF = "\x1b[?1049l"


def show_menu(canvas: Canvas) -> None:
    """Draw the legend and the menu just below the maze."""
    below = (canvas.rows + 1) // 2 + 1
    sys.stdout.write(f"\x1b[{below};1H\x1b[J\x1b[?25h")
    print(legend(canvas))
    if not canvas.gen.blocked:
        print("Note: maze too small to draw the '42' pattern")
    print(MENU)
    sys.stdout.flush()


def run(path: str) -> None:
    """Load the config, generate and save the maze, then run the menu."""
    cfg = MazeConfig.create_maze_config(path)
    # check the size first, so a huge maze is never built in memory
    size = fit_cell_size(cfg.width, cfg.height, cfg.cell)
    if size == 0:
        raise ValueError("terminal too small for this maze: "
                         "enlarge the window or zoom out")
    gen = MazeGenerator(
        cfg.width, cfg.height, cfg.entry, cfg.exit,
        perfect=cfg.perfect, seed=cfg.seed,
        algorithm=cfg.algorithm or "dfs",
    )
    canvas = Canvas(gen, size)
    # about 10 seconds of animation whatever the maze size
    delay = min(0.06, 10 / (cfg.width * cfg.height))

    sys.stdout.write(ALT_SCREEN_ON)
    try:
        def redraw(signum: int, frame: object) -> None:
            """Redraw everything when the terminal window is resized."""
            try:
                canvas.draw()
                show_menu(canvas)
            except RuntimeError:
                pass  # resized mid-drawing: skip, the next draw fixes it

        signal.signal(signal.SIGWINCH, redraw)

        generate(canvas, delay=delay)
        gen.save(cfg.output_file)
        path_shown = False
        color = 0
        while True:
            show_menu(canvas)
            choice = input("> ").strip().lower()
            if choice in ("q", ""):
                break
            if choice == "p":
                path_shown = not path_shown
                # about 3 seconds to draw the path, whatever its length
                step_delay = min(0.03, 3 / max(len(gen.solve()), 1))
                canvas.show_path(path_shown,
                                 step_delay if path_shown else 0.0)
                if path_shown:
                    canvas.explode(gen.exit)
            elif choice == "c":
                color = (color + 1) % len(WALL_COLORS)
                canvas.set_wall_color(WALL_COLORS[color])
            elif choice == "r":
                generate(canvas, delay=delay)
                gen.save(cfg.output_file)
                path_shown = False
    finally:
        # always leave the separate screen and restore the terminal
        sys.stdout.write("\x1b[0m\x1b[?25h" + ALT_SCREEN_OFF)
        sys.stdout.flush()


def main() -> int:
    """Check the arguments, run, and turn every error into a message."""
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt")
        return 1
    try:
        run(sys.argv[1])
    except ConfigError as e:
        print(e)
        return 1
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except OSError as e:
        print(f"Error: cannot write output file: {e}")
        return 1
    except (KeyboardInterrupt, EOFError):
        print()
    return 0


if __name__ == "__main__":
    main()
