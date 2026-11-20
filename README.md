*This project has been created as part of the 42 curriculum by shkholma, alehiany.*

# A-Maze-ing

## Description

A-Maze-ing reads a configuration file, generates a maze, writes it to an
output file in hexadecimal format, and displays it in the terminal.

- Each cell stores its 4 walls as bits (N=1, E=2, S=4, W=8), one hex digit
  per cell in the output file.
- A **"42" pattern** of closed cells is drawn near the center of the maze.
- In **perfect** mode there is exactly one path between any two cells.
  In **non-perfect** mode the maze has loops and no dead-end at all.
- The shortest path from entry to exit is computed and saved as N/E/S/W letters.
- The maze generator is a **reusable Python package** (`mazegen`) that can be
  installed with pip and used in other projects.

## Instructions

Requirements: Python 3.10+ and a terminal that supports 24-bit colors.

```bash
make install    # create .venv and install flake8 and mypy
make run        # run with config.txt
make debug      # run with pdb
make lint       # flake8 + mypy
make clean      # remove caches
```

Or directly:

```bash
python3 a_maze_ing.py config.txt
```

### Controls

| Key | Action |
|-----|--------|
| `r` | generate and display a new maze |
| `p` | show / hide the shortest path |
| `c` | change the wall color |
| `q` | quit |

### Build and install the `mazegen` package

```bash
.venv/bin/python -m pip install build
.venv/bin/python -m build --wheel --outdir .
.venv/bin/python -m pip install mazegen-1.0.0-py3-none-any.whl
```

## Configuration file

One `KEY=value` per line, no spaces. Lines starting with `#` are comments.

| Key | Required | Description | Example |
|-----|----------|-------------|---------|
| `WIDTH` | yes | number of columns (>= 1) | `WIDTH=20` |
| `HEIGHT` | yes | number of rows (>= 1) | `HEIGHT=15` |
| `ENTRY` | yes | entry cell as `x,y` (column,row) | `ENTRY=0,0` |
| `EXIT` | yes | exit cell as `x,y` (column,row) | `EXIT=19,14` |
| `OUTPUT_FILE` | yes | file where the maze is written | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | yes | `True/False`, `1/0`, `yes/no`, `y/n` | `PERFECT=True` |
| `ALGORITHM` | no | `dfs`, `prim`, `kruskal`, `hunt_and_kill` (default `dfs`) | `ALGORITHM=prim` |
| `SEED` | no | integer >= 0, same seed = same maze (default `42`) | `SEED=7` |
| `CELL` | no | cell size in pixels on screen (default `3`) | `CELL=6` |

Example:

```
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=0
ALGORITHM=dfs
SEED=42
CELL=6
```

Invalid values (wrong format, entry outside the grid, unknown key, ...) are
reported with a clear error message instead of a crash.

## Maze generation algorithm

**Default: randomized depth-first search (recursive backtracker).**
Starting from the entry, it walks to a random unvisited neighbor, opening the
wall between them, and backtracks when stuck, until every cell is visited.

**Why we chose it:**
- It is simple to understand and to implement with a stack.
- It produces long, winding corridors, which look like a real maze.
- It always produces a perfect maze, which is the base for both modes.
- It opens one wall at a time, which makes it easy to animate.

### Advanced features (bonuses)

- **Multiple algorithms:** DFS, Prim, Kruskal and hunt-and-kill, chosen with
  `ALGORITHM` in the config.
- **No dead-ends in non-perfect mode:** after generation, every dead-end gets
  one extra opening, without ever creating a 3x3 open area. The provided
  `maze_analyzer.py` confirms the result with 0 dead-ends.
- **Animation:** the maze is drawn while it is being generated, and the
  shortest path is drawn step by step, ending with a small firework at the exit.
- **Display:** colored terminal rendering with rounded tiles, a legend,
  wall color switching, and automatic resizing to fit the terminal window.

## Reusable code: `mazegen`

The `mazegen` package contains one class, `MazeGenerator`, with no display
code, so it can be imported in any project.

```python
from mazegen import MazeGenerator

gen = MazeGenerator(
    width=20, height=15,
    entry=(0, 0), exit=(14, 19),   # (row, col)
    perfect=True, seed=42, algorithm="dfs",
)
gen.generate()          # build the maze
gen.grid                # list of rows; each cell is an int, bits = walls
gen.blocked             # set of (row, col) cells of the "42" pattern
path = gen.solve()      # shortest path: list of (row, col), entry to exit
gen.save("maze.txt")    # write the output file
```

**Parameters:** `width`, `height`, `entry`, `exit`, `perfect` (default
`False`), `seed` (default `None` = random), `algorithm` (default `"dfs"`).

**Animation:** `generate()` takes an optional function `animation_step(a, b)`,
called after each wall opened between cells `a` and `b`.

## Team and project management

### Roles

| Member | Parts |
|--------|-------|
| shkholma | Config file parsing and validation, the original generation algorithms (DFS, Prim, Kruskal, hunt-and-kill), "42" pattern placement, first terminal renderer and animations, Makefile |
| alehiany | Reusable `mazegen` package (`MazeGenerator` class), new display and main program, packaging (`pyproject.toml`, wheel), LICENSE.md, README |

### Planning and how it evolved

- **Start:** the config parser, the algorithms and a terminal renderer were
  written first, each algorithm in its own file.
- **Middle:** to meet the reusability requirement, the algorithms, the "42"
  placement, dead-end removal and the solver were integrated into one
  `MazeGenerator` class, and the display was rewritten around it.
- **End:** testing with `maze_analyzer.py` showed the entry/exit coordinates
  had to be read and written as `x,y` (column,row); this was fixed in both the
  config parser and the output file. Then lint, packaging and documentation.

### What worked well and what could be improved

- **Worked well:** splitting the work (config / algorithms vs. package /
  display), testing every algorithm with the provided analyzer, and keeping the
  generator independent from the display.
- **Could be improved:** agreeing on the coordinate convention and on the
  final structure (one reusable class) at the very start would have avoided
  moving code later.

### Tools

Git and GitHub, VS Code, flake8, mypy, pytest, `build` (packaging), the
provided `maze_analyzer.py`, and Claude (AI assistant, see below).

## Resources

- [Maze generation algorithm (Wikipedia)](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [ANSI escape codes (Wikipedia)](https://en.wikipedia.org/wiki/ANSI_escape_code)
- [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [Python `random` documentation](https://docs.python.org/3/library/random.html)
- [Choose a License: MIT](https://choosealicense.com/licenses/mit/)

### How AI was used

AI was used as an assistant for:
- **Explanations:** walking through the subject, the existing code, bit
  operations, the algorithms and terminal rendering.
- **Restructuring:** guidance on moving the algorithms into the reusable
  `MazeGenerator` class and on the display design (colors, rounded tiles,
  thin path line, animation).
- **Review and debugging:** finding bugs (such as the `x,y` coordinate order),
  and git problems.
- **Packaging and docs:** `pyproject.toml`, building the wheel, the LICENSE
  and a first draft of this README.