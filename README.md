# A simple CLI to encrypt data in yaml files with `yamlpath` and `pyrage`

This tool aims to allow encrypting selected values (text) in a Yaml file using age encryption.

As age uses public/private key encryption, this allows to use the tool in a repository with committed
public key allowing developers to define new variables, while using the private key only where the
values are used.

## Usage

### Config file

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


### Encrypt

```yaml
yamlpage --config /path/to/config.yaml encrypt file.yaml
YAMLPAGE_CONFIG=/path/to/config.yaml yamlpage encrypt file.yaml

yamlpage --config /path/to/config.yaml encrypt --in-place file.yaml
yamlpage --config /path/to/config.yaml encrypt --output encrypted.yaml file.yaml
```

### Decrypt

```yaml
yamlpage --config /path/to/config.yaml --age-key age.key decrypt file.yaml
YAMLPAGE_CONFIG=/path/to/config.yaml YAMLPAGE_AGE_KEY=age.key yamlpage decrypt file.yaml

yamlpage --config /path/to/config.yaml --age-key age.key decrypt --in-place file.yaml
yamlpage --config /path/to/config.yaml --age-key age.key decrypt --output decrypted.yaml file.yaml
```
