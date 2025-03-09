import contextlib
import os
from pathlib import Path

import pyrage
import pytest
from ruamel.yaml import YAML

from yamlcrypt import (
    YamlCryptConfig,
    YamlCryptConfigNotFoundError,
    YamlCryptDuplicateIdentify,
    YamlCryptError,
)

DEFAULT_CONFIG = """yamlcrypt:
  identities: {}
  rules: []
"""


def default_no_rule_test_config(name, public, private):
    return f"""yamlcrypt:
  identities:
    {name}:
      private: {private}
      public: {public}
  rules: []
"""


def default_test_config():
    ident = pyrage.x25519.Identity.generate()
    public = ident.to_public()
    private = str(ident)
    return f"""
    yamlcrypt:
      identities:
        bla:
          public: '{public}'
          private: '{private}'
      rules:
        - yamlpath: "some.path.with.*"
          recipients:
            - bla
    """


@contextlib.contextmanager
def customized_env(values):
    env_backup = os.environ.copy()
    try:
        os.environ.update(values)
        yield
    finally:
        os.environ.clear()
        os.environ.update(env_backup)


def test_load_save_no_config(tmp_path):
    config = YamlCryptConfig()

    with pytest.raises(YamlCryptConfigNotFoundError):
        config.load(tmp_path / "config.yaml")
    assert "rules" in config.config
    assert len(config.config["rules"]) == 0
    assert "identities" in config.config
    assert len(config.config["identities"]) == 0

    config.save(tmp_path / "config.yaml")
    assert (tmp_path / "config.yaml").is_file()
    assert (tmp_path / "config.yaml").read_text() == DEFAULT_CONFIG

    config = YamlCryptConfig()
    config.load(tmp_path / "config.yaml")
    assert "rules" in config.config
    assert len(config.config["rules"]) == 0
    assert "identities" in config.config
    assert len(config.config["identities"]) == 0


def test_add_recipient_no_config(tmp_path):
    config = YamlCryptConfig()

    with pytest.raises(YamlCryptConfigNotFoundError):
        config.load(tmp_path / "config.yaml")
    config.add_recipient("bla")
    assert "bla" in config.config["identities"]
    assert "public" in config.config["identities"]["bla"]
    assert "private" in config.config["identities"]["bla"]

    config.save(tmp_path / "config.yaml")
    assert (tmp_path / "config.yaml").is_file()
    assert (tmp_path / "config.yaml").read_text() == default_no_rule_test_config(
        "bla",
        config.config["identities"]["bla"]["public"],
        config.config["identities"]["bla"]["private"],
    )

    config2 = YamlCryptConfig()
    config2.load(tmp_path / "config.yaml")
    assert (
        config2.config["identities"]["bla"]["public"]
        == config.config["identities"]["bla"]["public"]
    )
    assert (
        config2.config["identities"]["bla"]["private"]
        in config.config["identities"]["bla"]["private"]
    )


def test_add_recipient_already_exists(tmp_path):
    config = YamlCryptConfig()

    with pytest.raises(YamlCryptConfigNotFoundError):
        config.load(tmp_path / "config.yaml")
    config.add_recipient("bla")

    with pytest.raises(YamlCryptDuplicateIdentify):
        config.add_recipient("bla")

    config.save(tmp_path / "config.yaml")

    config = YamlCryptConfig()
    config.load(tmp_path / "config.yaml")
    with pytest.raises(YamlCryptDuplicateIdentify):
        config.add_recipient("bla")


def test_save_recipient_key(tmp_path):
    config = YamlCryptConfig()

    with pytest.raises(YamlCryptConfigNotFoundError):
        config.load(tmp_path / "config.yaml")
    config.add_recipient("bla")

    config.save(tmp_path / "config.yaml", recipients={"bla": tmp_path / "bla.yaml"})

    assert (tmp_path / "bla.yaml").exists()
    assert (tmp_path / "bla.yaml").is_file()

    private = [
        line
        for line in Path(tmp_path / "bla.yaml").read_text().splitlines()
        if line.startswith("AGE-SECRET-KEY-")
    ][0]

    config = YamlCryptConfig()
    config.load(tmp_path / "config.yaml")
    assert "private" not in config.config["identities"]["bla"]
    assert config.config["identities"]["bla"]["public"] == str(
        pyrage.x25519.Identity.from_str(private).to_public()
    )


def test_config_private_file(tmp_path):
    yaml = YAML(typ="safe")

    test_config = yaml.load(default_test_config())
    public = test_config["yamlcrypt"]["identities"]["bla"]["public"]
    private = test_config["yamlcrypt"]["identities"]["bla"]["private"]

    private_file = tmp_path / "private.key"
    private_file.write_text(f"# Some headings that should be ignored\n{private}\n")
    test_config["yamlcrypt"]["identities"]["bla"]["private"] = {"file": str(private_file)}

    with (tmp_path / "config.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(test_config, f)

    config = YamlCryptConfig()
    config.load(tmp_path / "config.yaml")

    assert str(config.recipient("bla")) == public
    assert str(config.identity("bla")) == private


def test_config_private_env_file(tmp_path):
    yaml = YAML(typ="safe")

    test_config = yaml.load(default_test_config())
    public = test_config["yamlcrypt"]["identities"]["bla"]["public"]
    private = test_config["yamlcrypt"]["identities"]["bla"]["private"]

    private_file = tmp_path / "private.key"
    private_file.write_text(f"# Some headings that should be ignored\n{private}\n")

    test_config["yamlcrypt"]["identities"]["bla"]["private"] = {
        "env": {"type": "path", "var": "MY_TEST_VAR"}
    }

    with (tmp_path / "config.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(test_config, f)

    with customized_env({"MY_TEST_VAR": str(private_file)}):
        config = YamlCryptConfig()
        config.load(tmp_path / "config.yaml")

        assert str(config.recipient("bla")) == public
        assert str(config.identity("bla")) == private


def test_config_private_env_val(tmp_path):
    yaml = YAML(typ="safe")

    test_config = yaml.load(default_test_config())
    public = test_config["yamlcrypt"]["identities"]["bla"]["public"]
    private = test_config["yamlcrypt"]["identities"]["bla"]["private"]

    test_config["yamlcrypt"]["identities"]["bla"]["private"] = {
        "env": {"type": "key", "var": "MY_TEST_VAR"}
    }

    with (tmp_path / "config.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(test_config, f)

    with customized_env({"MY_TEST_VAR": private}):
        config = YamlCryptConfig()
        config.load(tmp_path / "config.yaml")

        assert str(config.recipient("bla")) == public
        assert str(config.identity("bla")) == private


def test_config_private_default_env_val(tmp_path):
    yaml = YAML(typ="safe")

    test_config = yaml.load(default_test_config())
    public = test_config["yamlcrypt"]["identities"]["bla"]["public"]
    private = test_config["yamlcrypt"]["identities"]["bla"]["private"]

    del test_config["yamlcrypt"]["identities"]["bla"]["private"]

    with (tmp_path / "config.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(test_config, f)

    with customized_env({"YAMLCRYPT_IDENTITIES_KEY_BLA": private}):
        config = YamlCryptConfig()
        config.load(tmp_path / "config.yaml")

        assert str(config.recipient("bla")) == public
        assert str(config.identity("bla")) == private


def test_config_private_default_env_file(tmp_path):
    yaml = YAML(typ="safe")

    test_config = yaml.load(default_test_config())
    public = test_config["yamlcrypt"]["identities"]["bla"]["public"]
    private = test_config["yamlcrypt"]["identities"]["bla"]["private"]

    private_file = tmp_path / "private.key"
    private_file.write_text(f"# Some headings that should be ignored\n{private}\n")

    del test_config["yamlcrypt"]["identities"]["bla"]["private"]

    with (tmp_path / "config.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(test_config, f)

    with customized_env({"YAMLCRYPT_IDENTITIES_PATH_BLA": str(private_file)}):
        config = YamlCryptConfig()
        config.load(tmp_path / "config.yaml")

        assert str(config.recipient("bla")) == public
        assert str(config.identity("bla")) == private


def test_config_no_public(tmp_path):
    yaml = YAML(typ="safe")

    test_config = yaml.load(default_test_config())
    public = test_config["yamlcrypt"]["identities"]["bla"]["public"]
    private = test_config["yamlcrypt"]["identities"]["bla"]["private"]

    del test_config["yamlcrypt"]["identities"]["bla"]["public"]

    with (tmp_path / "config.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(test_config, f)

    config = YamlCryptConfig()
    config.load(tmp_path / "config.yaml")

    assert str(config.recipient("bla")) == public
    assert str(config.identity("bla")) == private


def test_config_no_private(tmp_path):
    yaml = YAML(typ="safe")

    test_config = yaml.load(default_test_config())
    public = test_config["yamlcrypt"]["identities"]["bla"]["public"]

    del test_config["yamlcrypt"]["identities"]["bla"]["private"]

    with (tmp_path / "config.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(test_config, f)

    config = YamlCryptConfig()
    config.load(tmp_path / "config.yaml")

    assert str(config.recipient("bla")) == public

    with pytest.raises(YamlCryptError) as error:
        config.identity("bla")
    assert error.value.args[0] == "Could not find identity config"
    assert error.value.args[1] == "bla"


def test_config_no_private_no_public(tmp_path):
    yaml = YAML(typ="safe")

    test_config = yaml.load(default_test_config())
    del test_config["yamlcrypt"]["identities"]["bla"]["private"]
    del test_config["yamlcrypt"]["identities"]["bla"]["public"]

    with (tmp_path / "config.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(test_config, f)

    config = YamlCryptConfig()
    config.load(tmp_path / "config.yaml")

    with pytest.raises(YamlCryptError) as error:
        config.recipient("bla")
    assert error.value.args[0] == "Could not find identity config"
    assert error.value.args[1] == "bla"

    with pytest.raises(YamlCryptError) as error:
        config.identity("bla")
    assert error.value.args[0] == "Could not find identity config"
    assert error.value.args[1] == "bla"
