from dataclasses import dataclass
from pathlib import Path
import re


# === constants ====
ALGORITHMS = {'dfs', 'hunt_and_kill', 'kruskal', 'prim'}
REQUIRED = {'WIDTH', 'HEIGHT', 'ENTRY', 'EXIT', 'OUTPUT_FILE'}
KEYWORDS = REQUIRED | {'PERFECT', 'ALGORITHM', 'SEED', 'CELL'}
_CFORMAT = re.compile(r"^([A-Z_]+)=(\S+)$")
_PFOUR = {(0, 0), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2), (3, 2)}
_PTWO = {(0, 4), (0, 5), (1, 5), (2, 4), (3, 4), (3, 5)}
_NDEFOUR = {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2), (4, 2), (5, 2)}
_NDETWO = {(0, 4), (0, 5), (1, 5), (2, 5), (3, 4), (4, 4), (5, 4), (5, 5)}
BG = (10, 50, 60)
WALL = (224, 163, 78)
S42 = (52, 55, 235)


# === class: errors and rewriting existing error messages ===

class ConfigError(Exception):
    pass


def _to_int(key: str, value: str) -> int:
    try:
        return int(value)
    except ValueError:
        raise ConfigError(f"{key}: '{value}' is not an integer") from None


def _to_bool(key: str, value: str) -> bool:
    if value in ("yes", "Yes", "true", "True", "1"):
        return True
    if value in ("no", "No", "false", "False", "0"):
        return False
    raise ConfigError(
        f"{key}: '{value}' is not a boolean "
        "(use only 'yes/no', 'Yes/No', 'true/false' 'True/False', '1/0')"
    )


def _to_point(key: str, value: str) -> tuple[int, int]:
    coords = value.split(',')
    if len(coords) != 2:
        raise ConfigError(f"{key}: expected 'row,col', got '{value}'")
    return _to_int(key, coords[0].strip()), _to_int(key, coords[1].strip())


# === class: maze configuration ===

@dataclass(frozen=True)
class MazeConfig:
    height: int
    width: int
    entry: tuple[int, int]
    exit: tuple[int, int]
    output_file: str
    perfect: bool = False
    algorithm: str | None = 'dfs'
    seed: int | None = 42
    cell: int = 3

    # automatic check after initialization
    def __post_init__(self) -> None:
        errors = []

        if self.height < 1:
            errors.append(f"HEIGHT must be >= 1, but got {self.height}")
        if self.width < 1:
            errors.append(f"HEIGHT must be >= 1, but got {self.width}")
        for key, (r, c) in (('ENTRY', self.entry), ('EXIT', self.exit)):
            if not (0 <= r < self.height and 0 <= c < self.width):
                errors.append(f"{key} {(r, c)} is outside the grid")
        if self.entry == self.exit:
            errors.append("ENTRY and EXIT must be different")
        if self.output_file is None:
            errors.append("OUTPUT_FILE cannot be empty")
        if self.algorithm is not None and self.algorithm not in ALGORITHMS:
            errors.append(f"ALGORITHM must be one of {ALGORITHMS}")
        if self.seed is not None and self.seed < 0:
            errors.append(f"SEED must be >= 0, but got {self.seed}")
        if self.cell < 1:
                errors.append(f"CELL must be >= 1, but got {self.cell}")

        if errors:
            raise ConfigError(
                "Invalid config:\n - " + "\n - ".join(errors)
            )

    # reading key=value pairs from config file
    @staticmethod
    def _read_pairs(path: Path) -> dict[str, str]:
        try:
            content = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise ConfigError(
                f"Config file not found: '{path}'"
            ) from None
        except UnicodeDecodeError:
            raise ConfigError(
                f"'{path}' is not a valid UTF-8 text file"
            ) from None
        except OSError as e:
            raise ConfigError(
                f"Cannot read '{path}': {e}"
            ) from None

        elems: dict[str, str] = {}
        for no, line in enumerate(content.splitlines(), start=1):
            if not line.strip() or line.startswith('#'):
                continue
            fit = _CFORMAT.match(line)
            if not fit:
                raise ConfigError(
                    f"Line {no}: expected 'KEY=value' or 'key=value1,value2' "
                    f"(no spaces), but got '{line}'"
                )
            key, _, value = line.partition('=')
            if key in elems:
                raise ConfigError(
                    f"Line {no}: duplicate key {key}"
                )
            elems[key] = value
        return elems

    # creation of config class
    @classmethod
    def create_maze_config(cls, path: str | Path) -> "MazeConfig":
        dct = cls._read_pairs(Path(path))

        missing = REQUIRED - dct.keys()
        if missing:
            raise ConfigError(
                f"Missing required keys: {missing}"
            )
        unknown = dct.keys() - KEYWORDS
        if unknown:
            raise ConfigError(
                f"Unknown keys: {unknown}"
            )

        return cls(
            height=_to_int('HEIGHT', dct['HEIGHT']),
            width=_to_int('WIDTH', dct['WIDTH']),
            entry=_to_point('ENTRY', dct['ENTRY']),
            exit=_to_point('EXIT', dct['EXIT']),
            output_file=dct['OUTPUT_FILE'],
            perfect=(
                _to_bool('PERFECT', dct['PERFECT'])
                if 'PERFECT' in dct else False
            ),
            seed=_to_int('SEED', dct['SEED']) if 'SEED' in dct else 42,
            cell=_to_int('CELL', dct['CELL']) if 'CELL' in dct else 3,
            algorithm=dct['ALGORITHM'] if 'ALGORITHM' in dct else 'dfs'
        )


# pixels: 
# each maze cell consists of CELLxCELL pixels 
# each wall consists of 1xCELL or CELLx1 pixels
class Pixel:
    def __init__(self, color: tuple[int, int, int], value: int) -> None:
        self.color = color
        self.value = value


# class: maze (array and pixels) 
# using config and 42 symbol in the middle
class Maze:
    def __init__(self, config: MazeConfig) -> None:
        self.config = config

        # maze map for printing output
        self.map: list[list[int]] = [
            [0b1111 for _ in range(config.width)]
            for _ in range(config.height)
        ]

        # maze pixel
        step = self.config.cell + 1
        wd = step * config.width + 1
        ht = step * config.height + 1
        self.pixels: list[list[Pixel]] = [
            [Pixel((0,0,0), 0b0000) for _ in range(wd)] for _ in range(ht)
        ]


    # locating 42 symbol (0b10000)
    def add42(self) -> None:
        (enr, enc) = self.config.entry
        (exr, exc) = self.config.exit
        if self.config.perfect:
            if self.config.width < 8 or self.config.height < 6:
                return None
            ih, iw = 0, 0
            for i in range(1, self.config.height):
                if 2 * (i + 2) > self.config.height or i + 5 > self.config.height:
                    break
                for j in range(1, self.config.width):
                    if 2 * (j + 3) > self.config.width or j + 7 > self.config.width:
                        break
                    if (enr - i, enc - j) in _PFOUR | _PTWO:
                        continue
                    if (exr - i, exc - j) in _PFOUR | _PTWO:
                        continue
                    ih, iw = i, j
            if (ih, iw) == (0, 0):
                return None
            for (i, j) in _PFOUR | _PTWO:
                self.map[ih + i][iw + j] = 0b10000
        else:
            if self.config.width < 8 or self.config.height < 8:
                return None
            ih, iw = 0, 0
            for i in range(1, self.config.height):
                if 2 * (i + 2) >= self.config.height or i + 7 > self.config.height:
                    break
                for j in range(1, self.config.width):
                    if 2 * (j + 3) > self.config.width or j + 7 > self.config.width:
                        break
                    if (enr - i, enc - j) in _NDEFOUR | _NDETWO:
                        continue
                    if (exr - i, exc - j) in _NDEFOUR | _NDETWO:
                        continue
                    ih, iw = i, j
            if (ih, iw) == (0, 0):
                return None
            for (i, j) in _NDEFOUR | _NDETWO:
                self.map[ih + i][iw + j] = 0b10000


    # creating pixels
    def pixel_init(self) -> None:
        cell = self.config.cell
        step = cell + 1
        wd = step * self.config.width + 1
        ht = step * self.config.height + 1
        for i in range(ht):
            for j in range(wd):
                if i % step == 0 or j % step == 0:
                    self.pixels[i][j].value = 0b10001 #wall
                    self.pixels[i][j].color = WALL
                else:
                    self.pixels[i][j].value = self.map[i // step][j // step]
                    self.pixels[i][j].color = BG
        for r in range(self.config.height):
            for c in range(self.config.width):
                if self.map[r][c] != 0b10000:
                    continue
                for i in range(step * r + 1, step * r + step):
                    for j in range(step * c + 1, step * c + step):
                        self.pixels[i][j].value = 0b10000 #42
                        self.pixels[i][j].color = S42 #42
                if self.map[r + 1][c] == 0b10000:
                    i = step * r + step
                    for j in range(step * c + 1, step * c + step):
                        self.pixels[i][j].value = 0b10000 #42
                        self.pixels[i][j].color = S42 #42
                if self.map[r][c + 1] == 0b10000:
                    j = step * c + step
                    for i in range(step * r + 1, step * r + step):
                        self.pixels[i][j].value = 0b10000 #42
                        self.pixels[i][j].color = S42 #42




    # printing maze map
    def __print_maze_map__(self) -> None:

        for i in range(self.config.height):
            for j in range(self.config.width):
                print("0123456789abcde*#$"[self.map[i][j]], end="")
            print()


    # printing maze pixel
    def __print_maze_pixel__(self) -> None:
        cell = self.config.cell
        step = cell + 1
        for i in range(step * self.config.height + 1):
            for j in range(step * self.config.width + 1):
                print("0123456789abcde*O#xQ"[self.pixels[i][j].value], end="")
            print()
