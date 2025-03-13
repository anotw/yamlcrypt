import base64
from dataclasses import dataclass
from pathlib import Path

import pyrage
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import (
    LiteralScalarString,
)
from yamlpath import Processor as YAMLProcessor
from yamlpath.common import Parsers

from yamlcrypt.config import YamlCryptConfig
from yamlcrypt.errors import YamlCryptError
from yamlcrypt.logger import logger
from yamlcrypt.node import YamlCryptNode


def split_string_at_width(text, width=80):
    return "\n".join(text[i : i + width] for i in range(0, len(text), width))


def encrypt_value(value, recipients):
    return base64.b64encode(pyrage.encrypt(value.encode("utf-8"), recipients)).decode("utf-8")


def decrypt_value(value, identities):
    return pyrage.decrypt(base64.b64decode(value), identities).decode("utf-8")


@dataclass
class YamlCryptProcessorArgs:
    input: Path
    output: Path | None = None


class YamlCryptProcessor:
    def __init__(self, args: YamlCryptProcessorArgs, config: YamlCryptConfig, log=None):
        self._args = args
        self._config = config
        self._log = log or logger()
        self.yaml = Parsers.get_yaml_editor()

        (self.yaml_data, doc_loaded) = Parsers.get_yaml_data(self.yaml, self._log, args.input)
        if not doc_loaded:
            raise YamlCryptError("Could not load input file", str(args.input))

        self.processor = YAMLProcessor(self._log, self.yaml_data)
        self.lines = args.input.read_text().splitlines()
        self.yaml.explicit_end = False
        for line in reversed(self.lines):
            if line.startswith("..."):
                self.yaml.explicit_end = True
            if len(line.strip()):
                break

    def __iterate_nodes(self):
        for rule in self._config.iterate_rules():
            for node_coordinate in self.processor.get_nodes(rule.yaml_path, mustexist=False):
                yield rule, node_coordinate

    def encrypt(self):
        should_dump = False
        for rule, node_coordinate in self.__iterate_nodes():
            starts = f"{rule.markup}["
            if isinstance(node_coordinate.node, str) and not node_coordinate.node.startswith(
                starts
            ):
                should_dump = True
                encrypted = encrypt_value(
                    YamlCryptNode.from_node_coordinate(
                        node_coordinate=node_coordinate, lines=self.lines
                    ).to_string(),
                    [self._config.recipient(name=recipient) for recipient in rule.recipients],
                )
                node_coordinate.parent[node_coordinate.parentref] = LiteralScalarString(
                    split_string_at_width(f"{rule.markup}[{encrypted}]")
                )
        if should_dump:
            self.dump()

    def decrypt(self):
        should_dump = False
        for rule, node_coordinate in self.__iterate_nodes():
            starts = f"{rule.markup}["
            ends = "]"
            if (
                isinstance(node_coordinate.node, str)
                and node_coordinate.node.startswith(starts)
                and node_coordinate.node.endswith(ends)
            ):
                should_dump = True
                decrypted = decrypt_value(
                    (node_coordinate.node[len(f"{rule.markup}[") : -1]).replace("\n", ""),
                    [self._config.identity(name=recipient) for recipient in rule.recipients],
                )
                node = YamlCryptNode.from_string(decrypted).to_rueyaml()
                if hasattr(node, "style"):
                    node_coordinate.parent[node_coordinate.parentref] = node
                else:
                    self.processor.set_value(node_coordinate.path, node)

        def post_process(data):
            return data.replace("\\n", "")

        if should_dump:
            self.dump(post_process=post_process)

    def dump(self, post_process=None):
        path = self._args.output or self._args.input

        def strip_document_end_marker(s):
            if not self.yaml.explicit_end and s.endswith("...\n"):
                return s[:-4]
            return s

        yaml = YAML(typ=["rt", "string"])
        yaml.explicit_start = self.yaml.explicit_start
        yaml.explicit_end = self.yaml.explicit_end
        ret = yaml.dump_to_string(self.yaml_data, add_final_eol=True)
        if post_process:
            ret = strip_document_end_marker(post_process(ret))

        path.write_text(ret)
