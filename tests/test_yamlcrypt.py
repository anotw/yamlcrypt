import contextlib
import os
from pathlib import Path
from types import SimpleNamespace

import pyrage
import pytest
from ruamel.yaml import YAML

from yamlcrypt import YamlCrypt, YamlCryptError

TEST_DATA_PATH = Path(__file__).parent / "data"


def default_test_config():
    ident = pyrage.x25519.Identity.generate()
    public = ident.to_public()
    private = str(ident)
    return f"""
    yamlcrypt:
      identities:
        age:
          public: '{public}'
          private: '{private}'
      rules:
        - yamlpath: "some.path.with.*"
          recipients:
            - age
    """


def get_test_files(test_case):
    base_path = Path(TEST_DATA_PATH / test_case)
    return sorted([file.name for file in base_path.iterdir() if file.is_file()])


def get_failing_files(test_case):
    return sorted([file.name for file in (TEST_DATA_PATH / test_case / "failing").iterdir()])


def get_working_files(test_case):
    failing = get_failing_files(test_case)
    return [file for file in get_test_files(test_case) if file not in failing]


def encryt_decrypt(tmp_path, config, test_path):
    yaml = YAML(typ="safe")

    with (tmp_path / "config.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(config, f)

    YamlCrypt(
        args=SimpleNamespace(
            config=tmp_path / "config.yaml",
            input_file=test_path,
            output=tmp_path / "encrypted.yaml",
        )
    ).encrypt()

    YamlCrypt(
        args=SimpleNamespace(
            config=tmp_path / "config.yaml",
            input_file=tmp_path / "encrypted.yaml",
            output=tmp_path / "decrypted.yaml",
        )
    ).decrypt()


@contextlib.contextmanager
def customized_env(values):
    env_backup = os.environ.copy()
    try:
        os.environ.update(values)
        yield
    finally:
        os.environ.clear()
        os.environ.update(env_backup)


@pytest.mark.parametrize("test_file", get_test_files("test_encrypt_decrypt"))
def test_encrypt_decrypt(tmp_path, test_file):
    (tmp_path / "config.yaml").write_text(default_test_config())

    test_path = TEST_DATA_PATH / "test_encrypt_decrypt" / test_file

    YamlCrypt(
        args=SimpleNamespace(
            config=tmp_path / "config.yaml",
            input_file=test_path,
            output=tmp_path / "encrypted.yaml",
        )
    ).encrypt()

    yaml = YAML(typ="safe")
    yaml_data = yaml.load((tmp_path / "encrypted.yaml").read_text())
    assert yaml_data
    assert yaml_data.get("some")
    assert yaml_data["some"].get("path")
    assert yaml_data["some"]["path"].get("with")

    YamlCrypt(
        args=SimpleNamespace(
            config=tmp_path / "config.yaml",
            input_file=tmp_path / "encrypted.yaml",
            output=tmp_path / "decrypted.yaml",
        )
    ).decrypt()
    print(str(tmp_path / "decrypted.yaml"))

    # Uncomment to dump the known to fail cases
    # if (tmp_path / "decrypted.yaml").read_text() != test_path.read_text():
    #     data = (tmp_path / "decrypted.yaml").read_text()
    #     (TEST_DATA_PATH / "test_encrypt_decrypt" / "failing" / test_file).write_text(data)

    # TODO parametrize to allow failing these ones without commenting the code
    if test_file in get_failing_files("test_encrypt_decrypt"):
        assert (tmp_path / "decrypted.yaml").read_text() == (
            TEST_DATA_PATH / "test_encrypt_decrypt" / "failing" / test_file
        ).read_text()
        return

    assert (tmp_path / "decrypted.yaml").read_text() == test_path.read_text()


def test_config_private_file(tmp_path):
    test_file = get_working_files("test_encrypt_decrypt")[0]
    yaml = YAML(typ="safe")

    test_path = TEST_DATA_PATH / "test_encrypt_decrypt" / test_file

    config = yaml.load(default_test_config())
    private = config["yamlcrypt"]["identities"]["age"]["private"]

    private_file = tmp_path / "private.key"
    private_file.write_text(f"# Some headings that should be ignored\n{private}\n")

    config["yamlcrypt"]["identities"]["age"]["private"] = {"file": str(private_file)}
    encryt_decrypt(tmp_path=tmp_path, config=config, test_path=test_path)
    assert (tmp_path / "decrypted.yaml").read_text() == test_path.read_text()


def test_config_private_env_file(tmp_path):
    test_file = get_working_files("test_encrypt_decrypt")[0]
    yaml = YAML(typ="safe")

    test_path = TEST_DATA_PATH / "test_encrypt_decrypt" / test_file

    config = yaml.load(default_test_config())
    private = config["yamlcrypt"]["identities"]["age"]["private"]

    private_file = tmp_path / "private.key"
    private_file.write_text(f"# Some headings that should be ignored\n{private}\n")

    config["yamlcrypt"]["identities"]["age"]["private"] = {
        "env": {"type": "path", "var": "MY_TEST_VAR"}
    }
    with customized_env({"MY_TEST_VAR": str(private_file)}):
        encryt_decrypt(tmp_path=tmp_path, config=config, test_path=test_path)
    assert (tmp_path / "decrypted.yaml").read_text() == test_path.read_text()


def test_config_private_env_val(tmp_path):
    test_file = get_working_files("test_encrypt_decrypt")[0]
    yaml = YAML(typ="safe")

    test_path = TEST_DATA_PATH / "test_encrypt_decrypt" / test_file

    config = yaml.load(default_test_config())
    private = config["yamlcrypt"]["identities"]["age"]["private"]

    config["yamlcrypt"]["identities"]["age"]["private"] = {
        "env": {"type": "key", "var": "MY_TEST_VAR"}
    }
    with customized_env({"MY_TEST_VAR": private}):
        encryt_decrypt(tmp_path=tmp_path, config=config, test_path=test_path)
    assert (tmp_path / "decrypted.yaml").read_text() == test_path.read_text()


def test_config_private_default_env_val(tmp_path):
    test_file = get_working_files("test_encrypt_decrypt")[0]
    yaml = YAML(typ="safe")

    test_path = TEST_DATA_PATH / "test_encrypt_decrypt" / test_file

    config = yaml.load(default_test_config())
    private = config["yamlcrypt"]["identities"]["age"]["private"]

    del config["yamlcrypt"]["identities"]["age"]["private"]

    with customized_env({"YAMLCRYPT_IDENTITIES_KEY_AGE": private}):
        encryt_decrypt(tmp_path=tmp_path, config=config, test_path=test_path)
    assert (tmp_path / "decrypted.yaml").read_text() == test_path.read_text()


def test_config_private_default_env_file(tmp_path):
    test_file = get_working_files("test_encrypt_decrypt")[0]
    yaml = YAML(typ="safe")

    test_path = TEST_DATA_PATH / "test_encrypt_decrypt" / test_file

    config = yaml.load(default_test_config())
    private = config["yamlcrypt"]["identities"]["age"]["private"]

    private_file = tmp_path / "private.key"
    private_file.write_text(f"# Some headings that should be ignored\n{private}\n")

    del config["yamlcrypt"]["identities"]["age"]["private"]

    with customized_env({"YAMLCRYPT_IDENTITIES_PATH_AGE": str(private_file)}):
        encryt_decrypt(tmp_path=tmp_path, config=config, test_path=test_path)
    assert (tmp_path / "decrypted.yaml").read_text() == test_path.read_text()


def test_config_no_public(tmp_path):
    test_file = get_working_files("test_encrypt_decrypt")[0]
    yaml = YAML(typ="safe")

    test_path = TEST_DATA_PATH / "test_encrypt_decrypt" / test_file

    config = yaml.load(default_test_config())
    del config["yamlcrypt"]["identities"]["age"]["public"]

    encryt_decrypt(tmp_path=tmp_path, config=config, test_path=test_path)
    assert (tmp_path / "decrypted.yaml").read_text() == test_path.read_text()


def test_config_no_private(tmp_path):
    test_file = get_working_files("test_encrypt_decrypt")[0]
    yaml = YAML(typ="safe")

    test_path = TEST_DATA_PATH / "test_encrypt_decrypt" / test_file

    config = yaml.load(default_test_config())
    del config["yamlcrypt"]["identities"]["age"]["private"]

    with (tmp_path / "config.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(config, f)

    YamlCrypt(
        args=SimpleNamespace(
            config=tmp_path / "config.yaml",
            input_file=test_path,
            output=tmp_path / "encrypted.yaml",
        )
    ).encrypt()

    with pytest.raises(YamlCryptError) as error:
        YamlCrypt(
            args=SimpleNamespace(
                config=tmp_path / "config.yaml",
                input_file=tmp_path / "encrypted.yaml",
                output=tmp_path / "decrypted.yaml",
            )
        ).decrypt()
    assert error.value.args[0] == "Could not find identity config"
    assert error.value.args[1] == "age"


def test_config_no_private_no_public(tmp_path):
    test_file = get_working_files("test_encrypt_decrypt")[0]
    yaml = YAML(typ="safe")

    test_path = TEST_DATA_PATH / "test_encrypt_decrypt" / test_file

    config = yaml.load(default_test_config())
    del config["yamlcrypt"]["identities"]["age"]["private"]
    del config["yamlcrypt"]["identities"]["age"]["public"]

    with (tmp_path / "config.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(config, f)

    with pytest.raises(YamlCryptError) as error:
        YamlCrypt(
            args=SimpleNamespace(
                config=tmp_path / "config.yaml",
                input_file=test_path,
                output=tmp_path / "encrypted.yaml",
            )
        ).encrypt()
    assert error.value.args[0] == "Could not find identity config"
    assert error.value.args[1] == "age"
