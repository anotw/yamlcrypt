from pathlib import Path

import pytest
from ruamel.yaml import YAML
from test_config import customized_env, default_test_config

from yamlcrypt.config import YamlCryptConfig
from yamlcrypt.errors import YamlCryptError
from yamlcrypt.processor import YamlCryptProcessor, YamlCryptProcessorArgs

TEST_DATA_PATH = Path(__file__).parent / "data"


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

    YamlCryptProcessor(
        args=YamlCryptProcessorArgs(
            input=test_path,
            output=tmp_path / "encrypted.yaml",
        ),
        config=YamlCryptConfig().load(tmp_path / "config.yaml"),
    ).encrypt()

    YamlCryptProcessor(
        args=YamlCryptProcessorArgs(
            input=tmp_path / "encrypted.yaml",
            output=tmp_path / "decrypted.yaml",
        ),
        config=YamlCryptConfig().load(tmp_path / "config.yaml"),
    ).decrypt()


@pytest.mark.parametrize("test_file", get_test_files("test_encrypt_decrypt"))
def test_encrypt_decrypt(tmp_path, test_file):
    (tmp_path / "config.yaml").write_text(default_test_config())

    test_path = TEST_DATA_PATH / "test_encrypt_decrypt" / test_file

    YamlCryptProcessor(
        args=YamlCryptProcessorArgs(
            input=test_path,
            output=tmp_path / "encrypted.yaml",
        ),
        config=YamlCryptConfig().load(tmp_path / "config.yaml"),
    ).encrypt()

    yaml = YAML(typ="safe")
    yaml_data = yaml.load((tmp_path / "encrypted.yaml").read_text())
    assert yaml_data
    assert yaml_data.get("some")
    assert yaml_data["some"].get("path")
    assert yaml_data["some"]["path"].get("with")

    YamlCryptProcessor(
        args=YamlCryptProcessorArgs(
            input=tmp_path / "encrypted.yaml",
            output=tmp_path / "decrypted.yaml",
        ),
        config=YamlCryptConfig().load(tmp_path / "config.yaml"),
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
    private = config["yamlcrypt"]["identities"]["bla"]["private"]

    private_file = tmp_path / "private.key"
    private_file.write_text(f"# Some headings that should be ignored\n{private}\n")

    config["yamlcrypt"]["identities"]["bla"]["private"] = {"file": str(private_file)}
    encryt_decrypt(tmp_path=tmp_path, config=config, test_path=test_path)
    assert (tmp_path / "decrypted.yaml").read_text() == test_path.read_text()


def test_config_private_env_file(tmp_path):
    test_file = get_working_files("test_encrypt_decrypt")[0]
    yaml = YAML(typ="safe")

    test_path = TEST_DATA_PATH / "test_encrypt_decrypt" / test_file

    config = yaml.load(default_test_config())
    private = config["yamlcrypt"]["identities"]["bla"]["private"]

    private_file = tmp_path / "private.key"
    private_file.write_text(f"# Some headings that should be ignored\n{private}\n")

    config["yamlcrypt"]["identities"]["bla"]["private"] = {
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
    private = config["yamlcrypt"]["identities"]["bla"]["private"]

    config["yamlcrypt"]["identities"]["bla"]["private"] = {
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
    private = config["yamlcrypt"]["identities"]["bla"]["private"]

    del config["yamlcrypt"]["identities"]["bla"]["private"]

    with customized_env({"YAMLCRYPT_IDENTITIES_KEY_BLA": private}):
        encryt_decrypt(tmp_path=tmp_path, config=config, test_path=test_path)
    assert (tmp_path / "decrypted.yaml").read_text() == test_path.read_text()


def test_config_private_default_env_file(tmp_path):
    test_file = get_working_files("test_encrypt_decrypt")[0]
    yaml = YAML(typ="safe")

    test_path = TEST_DATA_PATH / "test_encrypt_decrypt" / test_file

    config = yaml.load(default_test_config())
    private = config["yamlcrypt"]["identities"]["bla"]["private"]

    private_file = tmp_path / "private.key"
    private_file.write_text(f"# Some headings that should be ignored\n{private}\n")

    del config["yamlcrypt"]["identities"]["bla"]["private"]

    with customized_env({"YAMLCRYPT_IDENTITIES_PATH_BLA": str(private_file)}):
        encryt_decrypt(tmp_path=tmp_path, config=config, test_path=test_path)
    assert (tmp_path / "decrypted.yaml").read_text() == test_path.read_text()


def test_config_no_public(tmp_path):
    test_file = get_working_files("test_encrypt_decrypt")[0]
    yaml = YAML(typ="safe")

    test_path = TEST_DATA_PATH / "test_encrypt_decrypt" / test_file

    config = yaml.load(default_test_config())
    del config["yamlcrypt"]["identities"]["bla"]["public"]

    encryt_decrypt(tmp_path=tmp_path, config=config, test_path=test_path)
    assert (tmp_path / "decrypted.yaml").read_text() == test_path.read_text()


def test_config_no_private(tmp_path):
    test_file = get_working_files("test_encrypt_decrypt")[0]
    yaml = YAML(typ="safe")

    test_path = TEST_DATA_PATH / "test_encrypt_decrypt" / test_file

    config = yaml.load(default_test_config())
    del config["yamlcrypt"]["identities"]["bla"]["private"]

    with (tmp_path / "config.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(config, f)

    YamlCryptProcessor(
        args=YamlCryptProcessorArgs(
            input=test_path,
            output=tmp_path / "encrypted.yaml",
        ),
        config=YamlCryptConfig().load(tmp_path / "config.yaml"),
    ).encrypt()

    with pytest.raises(YamlCryptError) as error:
        YamlCryptProcessor(
            args=YamlCryptProcessorArgs(
                input=tmp_path / "encrypted.yaml",
                output=tmp_path / "decrypted.yaml",
            ),
            config=YamlCryptConfig().load(tmp_path / "config.yaml"),
        ).decrypt()
    assert error.value.args[0] == "Could not find identity config"
    assert error.value.args[1] == "bla"


def test_config_no_private_no_public(tmp_path):
    test_file = get_working_files("test_encrypt_decrypt")[0]
    yaml = YAML(typ="safe")

    test_path = TEST_DATA_PATH / "test_encrypt_decrypt" / test_file

    config = yaml.load(default_test_config())
    del config["yamlcrypt"]["identities"]["bla"]["private"]
    del config["yamlcrypt"]["identities"]["bla"]["public"]

    with (tmp_path / "config.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(config, f)

    with pytest.raises(YamlCryptError) as error:
        YamlCryptProcessor(
            args=YamlCryptProcessorArgs(
                input=test_path,
                output=tmp_path / "encrypted.yaml",
            ),
            config=YamlCryptConfig().load(tmp_path / "config.yaml"),
        ).encrypt()
    assert error.value.args[0] == "Could not find identity config"
    assert error.value.args[1] == "bla"
