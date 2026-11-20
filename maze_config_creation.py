"""Read and check the maze configuration file (KEY=VALUE per line)."""
from dataclasses import dataclass
from pathlib import Path
import re


# === constants ====
ALGORITHMS = {'dfs', 'hunt_and_kill', 'kruskal', 'prim'}
REQUIRED = {'WIDTH', 'HEIGHT', 'ENTRY', 'EXIT', 'OUTPUT_FILE', 'PERFECT'}
KEYWORDS = REQUIRED | {'ALGORITHM', 'SEED', 'CELL'}
_CFORMAT = re.compile(r"^([A-Z_]+)=(\S+)$")


# === class: errors and rewriting existing error messages ===
class ConfigError(Exception):
    """Raised when the config file is missing, malformed or invalid."""


def _to_int(key: str, value: str) -> int:
    """Convert value to an int.

    Args:
        key: Config key, used in the error message.
        value: Text to convert.

    Returns:
        The integer value.

    Raises:
        ConfigError: If value is not an integer.
    """
    try:
        return int(value)
    except ValueError:
        raise ConfigError(f"{key}: '{value}' is not an integer") from None


def _to_bool(key: str, value: str) -> bool:
    """Convert value (yes/no, true/false, 1/0, y/n) to a bool.

    Args:
        key: Config key, used in the error message.
        value: Text to convert.

    Returns:
        True or False.

    Raises:
        ConfigError: If value is not a known boolean word.
    """
    if value in ("yes", "Yes", "true", "True", "1", "Y", "y"):
        return True
    if value in ("no", "No", "false", "False", "0", "N", "n"):
        return False
    raise ConfigError(
        f"{key}: '{value}' is not a boolean (use only "
        "'y/n', 'Y/N', 'yes/no', 'Yes/No', 'true/false' 'True/False', '1/0')"
    )


def _to_point(key: str, value: str) -> tuple[int, int]:
    """Read 'x,y' (column, row) and return it as (row, col).

    Args:
        key: Config key, used in the error message.
        value: Text in the form 'x,y'.

    Returns:
        The point as (row, col).

    Raises:
        ConfigError: If value is not two integers separated by a comma.
    """
    coords = value.split(',')
    if len(coords) != 2:
        raise ConfigError(f"{key}: expected 'x,y', got '{value}'")
    x = _to_int(key, coords[0].strip())
    y = _to_int(key, coords[1].strip())
    return y, x


# === class: maze configuration ===
@dataclass(frozen=True)
class MazeConfig:
    """Validated maze settings read from the config file.

    Attributes:
        height: Number of rows.
        width: Number of columns.
        entry: Entry cell as (row, col).
        exit: Exit cell as (row, col).
        output_file: File where the maze is written.
        perfect: True for a perfect maze.
        algorithm: Generation algorithm name.
        seed: Random seed for reproducible mazes.
        cell: Cell size in pixels on screen.
    """

    height: int
    width: int
    entry: tuple[int, int]
    exit: tuple[int, int]
    output_file: str
    perfect: bool = False
    algorithm: str | None = 'dfs'
    seed: int | None = None
    cell: int = 3

    # automatic check after initialization
    def __post_init__(self) -> None:
        """Check every value and report all problems at once.

        Raises:
            ConfigError: If one or more values are invalid.
        """
        errors: list[str] = []

        if self.height < 1:
            errors.append(f"HEIGHT must be >= 1, but got {self.height}")
        if self.width < 1:
            errors.append(f"WIDTH must be >= 1, but got {self.width}")
        for key, (r, c) in (('ENTRY', self.entry), ('EXIT', self.exit)):
            if not (0 <= r < self.height and 0 <= c < self.width):
                errors.append(f"{key} {(c, r)} is outside the grid")
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
        """Read the file and return its KEY=value pairs.

        Empty lines and lines starting with '#' are skipped.

        Args:
            path: Path of the config file.

        Returns:
            A dict from key to its raw text value.

        Raises:
            ConfigError: If the file cannot be read, a line is malformed
                or a key appears twice.
        """
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
            if not line.strip() or line.strip().startswith('#'):
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
        """Read, convert and check the config file.

        Args:
            path: Path of the config file.

        Returns:
            The validated MazeConfig.

        Raises:
            ConfigError: If a key is missing or unknown, or a value is invalid.
        """
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
            perfect=_to_bool('PERFECT', dct['PERFECT']),
            seed=_to_int('SEED', dct['SEED']) if 'SEED' in dct else None,
            cell=_to_int('CELL', dct['CELL']) if 'CELL' in dct else 3,
            algorithm=dct['ALGORITHM'] if 'ALGORITHM' in dct else 'dfs'
        )
