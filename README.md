# A simple CLI to encrypt data in yaml files with `yamlpath` and `pyrage`

This tool aims to allow encrypting selected values (text) in a Yaml file using age encryption.

As age uses public/private key encryption, this allows to use the tool in a repository with committed
public key allowing developers to define new variables, while using the private key only where the
values are used.
