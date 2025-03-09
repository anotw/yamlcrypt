from importlib.metadata import PackageNotFoundError, version

from yamlcrypt.config import YamlCryptConfig
from yamlcrypt.errors import (
    YamlCryptConfigNotFoundError,
    YamlCryptDuplicateIdentify,
    YamlCryptError,
)
from yamlcrypt.yamlcrypt import YamlCrypt

try:
    __version__ = version("yamlcrypt")
except PackageNotFoundError:
    __version__ = "dev"

__all__ = [
    "YamlCrypt",
    "YamlCryptConfig",
    "YamlCryptConfigNotFoundError",
    "YamlCryptDuplicateIdentify",
    "YamlCryptError",
]
