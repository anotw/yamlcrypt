import base64
import os
from pathlib import Path
from types import SimpleNamespace

import ez_yaml
import pyrage
import ruamel.yaml
from ruamel.yaml.scalarstring import (
    DoubleQuotedScalarString,
    FoldedScalarString,
    LiteralScalarString,
    SingleQuotedScalarString,
)
from yamlpath import Processor as YAMLProcessor
from yamlpath import YAMLPath
from yamlpath.common import Parsers
from yamlpath.wrappers import ConsolePrinter


class YamlCryptError(Exception):
    pass


def split_string_at_width(text, width=80):
    return "\n".join(text[i : i + width] for i in range(0, len(text), width))


def encrypt_value(value, recipients):
    return base64.b64encode(pyrage.encrypt(value.encode("utf-8"), recipients)).decode("utf-8")


def decrypt_value(value, identities):
    return pyrage.decrypt(base64.b64decode(value), identities).decode("utf-8")


def format_env_var(env_type, name):
    return f"YAMLCRYPT_IDENTITIES_{env_type.upper()}_{name.upper()}"


def key_from_env(env_type, env_var):
    env_val = os.getenv(env_var)
    if not env_val:
        return ""
    if env_type == "key":
        return env_val
    elif env_type == "path":
        return Path(env_val).read_text()
    else:
        raise YamlCryptError("Unknown env variable type", env_type)


class YamlCryptNode:
    __slots__ = ("style", "data", "fold_pos")

    def __init__(self, style, data, fold_pos=None):
        self.style = style
        self.data = data
        self.fold_pos = fold_pos

    @classmethod
    def from_string(cls, data):
        obj = ez_yaml.to_object(data)
        return cls(style=obj["s"], data=obj["d"], fold_pos=obj.get("f"))

    @classmethod
    def from_node_coordinate(cls, node_coordinate, lines):
        def data_from_raw():
            key_name = node_coordinate.parentref
            val_line = node_coordinate.parent.lc.value(key_name)[0]
            val_col = node_coordinate.parent.lc.value(key_name)[1]

            for parent, parentref in reversed(node_coordinate.ancestry):
                keys = list(parent.keys())
                if parentref in keys[:-1]:
                    next_node = keys[keys.index(parentref) + 1]
                    next_node_parent = parent
                    break
            end_line = next_node_parent.lc.key(next_node)[0] - 1

            candidates = [lines[val_line][val_col:]] + [
                line.lstrip() for line in lines[val_line + 1 : end_line]
            ]
            data_lines = [line[:-1] if line[-1] == "\\" else line for line in candidates if line]
            data = "\n".join(data_lines)
            return data

        fold_pos = None
        if isinstance(node_coordinate.node, SingleQuotedScalarString) or isinstance(
            node_coordinate.node, DoubleQuotedScalarString
        ):
            data = data_from_raw()[1:-1]
        elif isinstance(node_coordinate.node, LiteralScalarString):
            data = str(node_coordinate.node)
        elif isinstance(node_coordinate.node, FoldedScalarString):
            data = str(node_coordinate.node)
            fold_pos = node_coordinate.node.fold_pos
        else:
            data = node_coordinate.node

        return cls(
            style=getattr(node_coordinate.node, "style", None),
            data=data,
            fold_pos=fold_pos,
        )

    def to_dict(self):
        d = {"s": self.style, "d": self.data}
        if self.fold_pos:
            d["f"] = self.fold_pos
        return d

    def to_string(self):
        return ez_yaml.to_string(self.to_dict())

    def to_rueyaml(self):
        fct = None
        if self.style is None:
            fct = str
        elif self.style == "'":
            fct = SingleQuotedScalarString
        elif self.style == '"':
            fct = DoubleQuotedScalarString
        elif self.style == ">":
            node = FoldedScalarString(self.data)
            node.fold_pos = self.fold_pos or []
            return node
        elif self.style == "|":
            fct = LiteralScalarString
        return fct(self.data)


class YamlCrypt:
    DEFAULT_MARKUP = "YamlCrypt"

    def __init__(self, args):
        self.recipients = {}
        self.identities = {}

        self.args = args
        self.log = ConsolePrinter(SimpleNamespace(quiet=True, verbose=False, debug=False))
        self.yaml = Parsers.get_yaml_editor()

        (self._config, doc_loaded) = Parsers.get_yaml_data(self.yaml, self.log, args.config)
        if not doc_loaded:
            raise YamlCryptError("Could not load config file")

        (self.yaml_data, doc_loaded) = Parsers.get_yaml_data(self.yaml, self.log, args.input_file)
        if not doc_loaded:
            raise YamlCryptError("Could not load config file")

        self.processor = YAMLProcessor(self.log, self.yaml_data)
        self.lines = args.input_file.read_text().splitlines()
        self.yaml.explicit_end = False
        for line in reversed(self.lines):
            if line.startswith("..."):
                self.yaml.explicit_end = True
            if len(line.strip()):
                break

    @property
    def config(self):
        return self._config["yamlcrypt"]

    def __iterate_nodes(self):
        for rule in self.config.get("rules", []):
            yaml_path = YAMLPath(rule["yamlpath"])
            for node_coordinate in self.processor.get_nodes(yaml_path, mustexist=True):
                yield rule, node_coordinate

    def identity(self, name):
        key = None
        if name not in self.identities:
            private = self.config["identities"][name].get("private")
            if isinstance(private, dict):
                if "file" in private:
                    key = Path(private["file"]).read_text()
                elif "env" in private:
                    env_type = private["env"].get("type", "key")
                    key = key_from_env(
                        env_type=env_type,
                        env_var=private["env"].get(
                            "var", format_env_var(env_type=env_type, name=name)
                        ),
                    )
            elif isinstance(private, str):
                key = private

            if not key:
                for env_type in ["key", "path"]:
                    key = key_from_env(
                        env_type=env_type,
                        env_var=format_env_var(env_type=env_type, name=name),
                    )
                    if key:
                        break
            keys = [line for line in key.splitlines() if line.startswith("AGE-SECRET-KEY-")]
            if keys:
                key = keys[0]

            if not key:
                raise YamlCryptError("Could not find identity config", name)

            self.identities[name] = pyrage.x25519.Identity.from_str(key)
        return self.identities[name]

    def recipient(self, name):
        if name not in self.recipients:
            public = self.config["identities"][name].get("public")
            if public:
                self.recipients[name] = pyrage.x25519.Recipient.from_str(public)
            else:
                self.recipients[name] = self.identity(name).to_public()
        return self.recipients[name]

    def encrypt(self):
        for rule, node_coordinate in self.__iterate_nodes():
            markup = rule.get("markup", self.DEFAULT_MARKUP)
            starts = f"{markup}["
            if isinstance(node_coordinate.node, str) and not node_coordinate.node.startswith(
                starts
            ):
                encrypted = encrypt_value(
                    YamlCryptNode.from_node_coordinate(
                        node_coordinate=node_coordinate, lines=self.lines
                    ).to_string(),
                    [self.recipient(name=recipient) for recipient in rule["recipients"]],
                )
                node_coordinate.parent[node_coordinate.parentref] = LiteralScalarString(
                    split_string_at_width(f"{markup}[{encrypted}]")
                )
        self.dump()

    def decrypt(self):
        for rule, node_coordinate in self.__iterate_nodes():
            markup = rule.get("markup", self.DEFAULT_MARKUP)
            starts = f"{markup}["
            ends = "]"
            if (
                isinstance(node_coordinate.node, str)
                and node_coordinate.node.startswith(starts)
                and node_coordinate.node.endswith(ends)
            ):
                decrypted = decrypt_value(
                    (node_coordinate.node[len(f"{markup}[") : -1]).replace("\n", ""),
                    [self.identity(name=recipient) for recipient in rule["recipients"]],
                )
                node = YamlCryptNode.from_string(decrypted).to_rueyaml()
                if hasattr(node, "style"):
                    node_coordinate.parent[node_coordinate.parentref] = node
                else:
                    self.processor.set_value(node_coordinate.path, node)

        def post_process(data):
            return data.replace("\\n", "")

        self.dump(post_process=post_process)

    def dump(self, post_process=None):
        path = self.args.output
        if not path and self.args.in_place:
            path = self.args.input_file

        def strip_document_end_marker(s):
            if not self.yaml.explicit_end and s.endswith("...\n"):
                return s[:-4]
            return s

        yaml = ruamel.yaml.YAML(typ=["rt", "string"])
        yaml.explicit_start = self.yaml.explicit_start
        yaml.explicit_end = self.yaml.explicit_end
        ret = yaml.dump_to_string(self.yaml_data, add_final_eol=True)
        if post_process:
            ret = strip_document_end_marker(post_process(ret))

        if path:
            path.write_text(ret)
        else:
            print(ret)
