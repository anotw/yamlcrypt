from pathlib import Path
from types import SimpleNamespace

import pytest

from yamlcrypt.processor import YamlCryptProcessorArgs
from yamlcrypt.utils import namespace_to_dataclass


@pytest.mark.parametrize(
    ("input", "output"),
    [
        (
            SimpleNamespace(input=Path("/tmp/test-path")),
            YamlCryptProcessorArgs(input=Path("/tmp/test-path")),
        ),
        (
            SimpleNamespace(input=Path("/tmp/test-path")),
            YamlCryptProcessorArgs(input=Path("/tmp/test-path"), output=None),
        ),
        (
            SimpleNamespace(input=Path("/tmp/test-path"), output=Path("/tmp/output-path")),
            YamlCryptProcessorArgs(input=Path("/tmp/test-path"), output=Path("/tmp/output-path")),
        ),
        (
            SimpleNamespace(input=Path("/tmp/test-path"), random=12345),
            YamlCryptProcessorArgs(input=Path("/tmp/test-path"), output=None),
        ),
    ],
)
def test_namespace_to_dataclass(input, output):
    assert namespace_to_dataclass(input, type(output)) == output
