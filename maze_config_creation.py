from dataclasses import dataclass
from pathlib import Path
import re


# === constants ====
ALGORITHMS = {'dfs', 'hunt_and_kill', 'kruskal', 'prim'}
REQUIRED = {'WIDTH', 'HEIGHT', 'ENTRY', 'EXIT', 'OUTPUT_FILE'}
KEYWORDS = REQUIRED | {'PERFECT', 'ALGORITHM', 'SEED'}
_CFORMAT = re.compile(r"^([A-Z_]+)=(\S+)$")
_PFOUR = {(0, 0), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2), (3, 2)}
_PTWO = {(0, 4), (0, 5), (1, 5), (2, 4), (3, 4),(3, 5)}
_NDEFOUR = {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2), (4, 2), (5, 2)}
_NDETWO = {(0, 4), (0, 5), (1, 5), (2, 5), (3, 4),(4, 4), (5, 4), (5, 5)}


# === class: errors and rewriting existing error messages ===

class ConfigError(Exception):
    pass

def _to_int(key: str, value: str) -> int:
    try:
        return int(value)
    except ValueError:
        raise ConfigError(f"{key}: '{value}' is not an integer") from None

def _to_bool(key: str, value: bool) -> bool:
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

    # automatic check after initialization
    def __post_init__(self):
        errors = []

        if self.height < 1:
            errors.append(f"HEIGHT must be >= 1, but got {self.height}")
        if self.width < 1:
            errors.append(f"HEIGHT must be >= 1, but got {self.width}")
        for key, (r, c) in (('ENTRY', self.entry), ('EXIT', self.exit)):
            if not (0 <= r < self.height and 0 <= c < self.width):
                errors.append(f"{key} {(r,c)} is outside the grid")
        if self.entry == self.exit:
            errors.append("ENTRY and EXIT must be different")
        if self.output_file == None:
            errors.append("OUTPUT_FILE cannot be empty")
        if self.algorithm != None and self.algorithm not in ALGORITHMS:
            errors.append(f"ALGORITHM must be one of {ALGORITHMS}")
        if self.seed != None and self.seed < 0:
            errors.append(f"SEED must be >= 0, but got {self.seed}")
        
        if errors:
            raise ConfigError("Invalid config:\n - " + "\n - ".join(errors))


    # reading key=value pairs from config file
    @staticmethod
    def _read_pairs(path: Path) -> dict[str, str]:
        try:
            content = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise ConfigError(f"Config file not found: '{path}'") from None
        except UnicodeDecodeError:
            raise ConfigError(f"'{path}' is not a valid UTF-8 text file") from None
        except OSError as e:
            raise ConfigError(f"Cannot read '{path}': {e}") from None

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
                raise ConfigError(f"Line {no}: duplicate key {key}")
            elems[key] = value
        return elems


    # creation of config class
    @classmethod
    def create_maze_config(cls, path: str | Path) -> "MazeConfig":
        dct = cls._read_pairs(Path(path))

        missing = REQUIRED - dct.keys()
        if missing:
            raise ConfigError(f"Missing required keys: {missing}")
        unknown = dct.keys() - KEYWORDS
        if unknown:
            raise ConfigError(f"Unknown keys: {unknown}")
        
        return cls(
            height=_to_int('HEIGHT', dct['HEIGHT']),
            width=_to_int('WIDTH', dct['WIDTH']),
            entry=_to_point('ENTRY', dct['ENTRY']),
            exit=_to_point('EXIT', dct['EXIT']),
            output_file=dct['OUTPUT_FILE'],
            perfect=_to_bool('PERFECT', dct['PERFECT']) if 'PERFECT' in dct else False,
            seed=_to_int('SEED', dct['SEED']) if 'SEED' in dct else 42,
            algorithm=dct['ALGORITHM'] if 'ALGORITHM' in dct else 'dfs'
        )


# class: maze (array) with just-read config and 42 symbol in the middle
class Maze:
    def __init__(self, config: MazeConfig) -> None:
        self.config = config
        
        # 2d grid: W (west), S (south), E (east), N (north) all in 0 or 1
        self.array: list[list[int]] = [
            [0b0000 for _ in range(config.width)]
            for _ in range(config.height)
        ]

        # locating entry (O) and exit (E) if needed
        # self.array[config.entry[0]][config.entry[1]] = 0b10001
        # self.array[config.exit[0]][config.exit[1]] = 0b10010

        # locating 42 symbol (f)
        if config.perfect:
            if config.width < 8 or config.height < 6:
                return None
            ih, iw = 0, 0
            for i in range(1, config.height):
                if 2 * (i + 2) > config.height or i + 5 > config.height:
                    break 
                for j in range(1, config.width):
                    if 2 * (j + 3) > config.width or j + 7 > config.width:
                        break
                    if (config.entry[0] - i, config.entry[1] - j) in _PFOUR | _PTWO:
                        continue
                    if (config.exit[0] - i, config.exit[1] - j) in _PFOUR | _PTWO:
                        continue
                    ih, iw = i, j
            if (ih, iw) == (0, 0):
                return None
            for (i, j) in _PFOUR | _PTWO:
                self.array[ih + i][iw + j] = 0b1111
        else:
            if config.width < 8 or config.height < 8:
                return None
            ih, iw = 0, 0
            for i in range(1, config.height):
                if 2 * (i + 2) >= config.height or i + 7 > config.height:
                    break 
                for j in range(1, config.width):
                    if 2 * (j + 3) > config.width or j + 7 > config.width:
                        break
                    if (config.entry[0] - i, config.entry[1] - j) in _NDEFOUR | _NDETWO:
                        continue
                    if (config.exit[0] - i, config.exit[1] - j) in _NDEFOUR | _NDETWO:
                        continue
                    ih, iw = i, j
            if (ih, iw) == (0, 0):
                return None
            for (i, j) in _NDEFOUR | _NDETWO:
                self.array[ih + i][iw + j] = 0b1111

    # printing maze
    def __print_maze__(self) -> None:
        for i in range(self.config.height):
            for j in range(self.config.width):
                print("0123456789abcdef"[self.array[i][j]], end="")
            print()
