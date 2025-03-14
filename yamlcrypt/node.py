from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import (
    DoubleQuotedScalarString,
    FoldedScalarString,
    LiteralScalarString,
    SingleQuotedScalarString,
)


def get_yaml():
    yaml = YAML(typ=["rt", "string"])
    yaml.explicit_end = False
    yaml.explicit_start = False
    return yaml


class YamlCryptNode:
    __slots__ = ("style", "data", "fold_pos")

    def __init__(self, style, data, fold_pos=None):
        self.style = style
        self.data = data
        self.fold_pos = fold_pos

    @classmethod
    def from_string(cls, data):
        obj = get_yaml().load(data)
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
        return get_yaml().dump_to_string(self.to_dict(), add_final_eol=False)

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
