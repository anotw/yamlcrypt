# A simple CLI to encrypt data in yaml files with `yamlpath` and `pyrage`

This tool aims to allow encrypting selected values (text) in a Yaml file using age encryption.

As age uses public/private key encryption, this allows to use the tool in a repository with committed
public key allowing developers to define new variables, while using the private key only where the
values are used.

> Please beware that current config file format would allow to defined multiple recipients for a rule
> this is not currently supported.

## Usage

### Add a recipient

For `yamlcrypt` to work it will need a [config file](#config-file) with at least one recipient defined.

Keys can be generated with the `age` CLI directly otherwise the `yamlcrypt` `recipient add` command
can be used.

To generate/add a key pair for the recipient `admin` use:

```
yamlcrypt --config /path/to/config.yaml recipient add admin
yamlcrypt --config /path/to/config.yaml recipient add admin --key-file /path/to/admin.keyfile
```

> When no file already exist on the provided config file path then a default config file is generated.
> If the file already existed the new recipient is simply added to the existing file.

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
file for the encryption scenarios.

For the decryption scenarios, the private key do not need to be present in the config file. The key
can be provided though a separate config file or and env variable.

The below sections describe the different supported options.

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

When no `private` field is defined in the config file, the private key will be search in
an environment variable with named built by convention.

If the variable `YAMLCRYPT_IDENTITIES_PATH_{upper case identity name}` is found the variable is
interpreted as the path to the private key for that identity.

If the variable `YAMLCRYPT_IDENTITIES_KEY_{upper case identity name}` is found the variable is
interpreted as the private key itself.

For example for an identity / recipient with the name `age` the default variables would be:
  - `YAMLCRYPT_IDENTITIES_PATH_AGE`: The path to the private file for the identity `age`
  - `YAMLCRYPT_IDENTITIES_KEY_AGE`: The private key directly

## Docker

The `yamlcrypt` CLI is as well pre-built inside the docker image `ghcr.io/anotw/yamlcrypt`.

In order to use it the location of the config file and the files to be encrypted must be mounted
as volumes.

```console
$ docker run -it --rm -v $PWD:$PWD -w $PWD ghcr.io/anotw/yamlcrypt encrypt $PWD/file.yaml
```
