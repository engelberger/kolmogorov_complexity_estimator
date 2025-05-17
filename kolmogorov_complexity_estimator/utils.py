# String ops, logging setup, config loading, common constants 

import logging
import json
from pathlib import Path
from typing import Union, Dict


def get_binary_complement(s: str) -> str:
    """
    Return the bitwise complement of a binary string (0 <-> 1).

    :param s: Input binary string.
    :return: Complemented binary string.
    """
    complement_map = {'0': '1', '1': '0'}
    return ''.join(complement_map.get(ch, ch) for ch in s)


def reverse_string(s: str) -> str:
    """
    Return the reverse of the input string.

    :param s: Input string.
    :return: Reversed string.
    """
    return s[::-1]


def setup_logging(level: Union[str, int] = 'INFO') -> None:
    """
    Configure the root logger with a standard format and level.

    :param level: Logging level as a string (e.g., 'DEBUG', 'INFO') or numeric.
    """
    # Determine numeric level
    if isinstance(level, str):
        numeric_level = getattr(logging, level.upper(), logging.INFO)
    else:
        numeric_level = level
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )


def load_config_file(path: str) -> Dict:
    """
    Load configuration from JSON, YAML, or TOML file into a dictionary.

    :param path: Path to the config file.
    :return: Configuration dictionary.
    """
    config_path = Path(path)
    ext = config_path.suffix.lower()
    if ext == '.json':
        with open(config_path) as f:
            return json.load(f)
    elif ext in ('.yaml', '.yml'):
        try:
            import yaml  # type: ignore
        except ImportError:
            raise ImportError('PyYAML is required to load YAML config files')
        with open(config_path) as f:
            return yaml.safe_load(f)
    elif ext == '.toml':
        try:
            import toml  # type: ignore
        except ImportError:
            raise ImportError('toml package is required to load TOML config files')
        with open(config_path) as f:
            return toml.load(f)
    else:
        raise ValueError(f'Unsupported config file format: {ext}') 