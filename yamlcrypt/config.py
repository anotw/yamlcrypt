import os
from dataclasses import dataclass
from pathlib import Path

import pyrage
from ruamel.yaml import YAML
from yamlpath import YAMLPath
from yamlpath.common import Parsers

from yamlcrypt.errors import (
    YamlCryptConfigNotFoundError,
    YamlCryptDuplicateIdentify,
    YamlCryptError,
)
from yamlcrypt.logger import logger

PRIVATE_KEY_FORMAT = """# The private key for the recipient {recipient}
{private}
"""


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


def format_env_var(env_type, name):
    return f"YAMLCRYPT_IDENTITIES_{env_type.upper()}_{name.upper()}"


@dataclass
class YamlCryptRule:
    yaml_path: YAMLPath
    markup: str
    recipients: list[str]


class YamlCryptConfig:
    DEFAULT_MARKUP = "YamlCrypt"

    def __init__(self, log=None):
        self._config = {"yamlcrypt": {"identities": {}, "rules": []}}
        self._yaml = Parsers.get_yaml_editor()
        self._log = log or logger()
        self._recipients = {}
        self._identities = {}

    @property
    def config(self):
        return self._config["yamlcrypt"]

    def iterate_rules(self):
        for rule in self.config.get("rules", []):
            yield YamlCryptRule(
                yaml_path=YAMLPath(rule["yamlpath"]),
                markup=rule.get("markup", self.DEFAULT_MARKUP),
                recipients=rule["recipients"],
            )

    def load(self, path: Path):
        if not path.exists() or not path.is_file():
            raise YamlCryptConfigNotFoundError("File not found", path)

        (tmp, doc_loaded) = Parsers.get_yaml_data(self._yaml, self._log, path)
        if not doc_loaded:
            raise YamlCryptError("Could not load config file", path)

        self._config = tmp
        return self

    def save(self, path, recipients: dict[str, Path] | None = None):
        yaml = YAML(typ="safe")
        yaml.default_flow_style = False
        config = self._config.copy()
        for recipient, recipient_key_file in (recipients or {}).items():
            private = config["yamlcrypt"]["identities"][recipient]["private"]
            recipient_key_file.write_text(
                PRIVATE_KEY_FORMAT.format(recipient=recipient, private=private)
            )
            del config["yamlcrypt"]["identities"][recipient]["private"]
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(config, f)
        return self

    def identity(self, name):
        key = None
        if name not in self._identities:
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

            self._identities[name] = pyrage.x25519.Identity.from_str(key)
        return self._identities[name]

    def recipient(self, name):
        if name not in self._recipients:
            public = self.config["identities"][name].get("public")
            if public:
                self._recipients[name] = pyrage.x25519.Recipient.from_str(public)
            else:
                self._recipients[name] = self.identity(name).to_public()
        return self._recipients[name]

    def add_recipient(self, name):
        if name in self.config.get("identities"):
            raise YamlCryptDuplicateIdentify("An identity with this name already exists", name)

        ident = pyrage.x25519.Identity.generate()
        self.config["identities"][name] = {"public": str(ident.to_public()), "private": str(ident)}
        return self
