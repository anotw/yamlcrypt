# A simple CLI to encrypt data in yaml files with `yamlpath` and `pyrage`

This tool aims to allow encrypting selected values (text) in a YAML file using age encryption.

As age uses public/private key encryption, this allows the tool to be used in a repository with a committed
public key, enabling developers to define new variables while using the private key only where the
values are used.

> Please beware that the current config file format allows defining multiple recipients for a rule,
> but this is not currently supported.

## Usage

### Add a recipient

For `yamlcrypt` to work, it will need a [config file](#config-file) with at least one recipient defined.

Keys can be generated with the `age` CLI directly; otherwise, the `yamlcrypt` `recipient add` command
can be used.

To generate/add a key pair for the recipient `admin` use:

```console
yamlcrypt --config /path/to/config.yaml recipient add admin
yamlcrypt --config /path/to/config.yaml recipient add admin --key-file /path/to/admin.keyfile
```

> When no file already exists at the provided config file path, a default config file is generated.
> If the file already existed, the new recipient is simply added to the existing file.

### Encrypt

```console
yamlcrypt --config /path/to/config.yaml encrypt file.yaml
YAMLCRYPT_CONFIG=/path/to/config.yaml yamlcrypt encrypt file.yaml

yamlcrypt --config /path/to/config.yaml encrypt --in-place file.yaml
yamlcrypt --config /path/to/config.yaml encrypt --output encrypted.yaml file.yaml
```

### Decrypt

```console
yamlcrypt --config /path/to/config.yaml --age-key age.key decrypt file.yaml
YAMLCRYPT_CONFIG=/path/to/config.yaml YAMLCRYPT_AGE_KEY=age.key yamlcrypt decrypt file.yaml

yamlcrypt --config /path/to/config.yaml --age-key age.key decrypt --in-place file.yaml
yamlcrypt --config /path/to/config.yaml --age-key age.key decrypt --output decrypted.yaml file.yaml
```

### Config file

Because `yamlcrypt` uses `age` asymmetric encryption, the private keys are not needed in the config
file for encryption scenarios.

For decryption scenarios, the private key does not need to be present in the config file. The key
can be provided through a separate config file or an env variable.

The sections below describe the different supported options.

#### All values in the config

```yaml
yamlcrypt:
  identities:
    age:
      public: '{public}'
      private: '{private}'
  rules:
    - yamlpath: "some.path.with.*"
      recipients:
        - age
```

#### Private key in a file

```yaml
yamlcrypt:
  identities:
    age:
      public: '{public}'
      private:
        file: /path/to/file/with/private/key

  rules:
    - yamlpath: "some.path.with.*"
      recipients:
        - age
```

#### Var with path to private key

```yaml
yamlcrypt:
  identities:
    age:
      public: '{public}'
      private:
        env:
          type: path
          var: ENV_POINTING_TO_FILE

  rules:
    - yamlpath: "some.path.with.*"
      recipients:
        - age
```

#### Var with private key

```yaml
yamlcrypt:
  identities:
    age:
      public: '{public}'
      private:
        env:
          type: key
          var: ENV_WITH_PRIVATE_KEY

  rules:
    - yamlpath: "some.path.with.*"
      recipients:
        - age
```

#### Default var handling

When no `private` field is defined in the config file, the private key will be searched in
an environment variable named by convention.

If the variable `YAMLCRYPT_IDENTITIES_PATH_{upper case identity name}` is found, the variable is
interpreted as the path to the private key for that identity.

If the variable `YAMLCRYPT_IDENTITIES_KEY_{upper case identity name}` is found, the variable is
interpreted as the private key itself.

For example, for an identity/recipient with the name `age`, the default variables would be:
  - `YAMLCRYPT_IDENTITIES_PATH_AGE`: The path to the private file for the identity `age`
  - `YAMLCRYPT_IDENTITIES_KEY_AGE`: The private key directly

## Docker

The `yamlcrypt` CLI is also pre-built inside the Docker image `ghcr.io/anotw/yamlcrypt`.

In order to use it, the location of the config file and the files to be encrypted must be mounted
as volumes.

```console
$ docker run -it --rm -v $PWD:$PWD -w $PWD ghcr.io/anotw/yamlcrypt encrypt $PWD/file.yaml
```
