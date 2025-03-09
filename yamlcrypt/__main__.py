import argparse
import os
from pathlib import Path

from yamlcrypt.yamlcrypt import YamlCrypt


class EnvDefaultConfig(argparse.Action):
    """Custom argparse Action that defaults to the environment variable YAMLCRYPT_CONFIG."""

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if values is None:
            values = os.getenv("YAMLCRYPT_CONFIG")
        if values is None:
            parser.error(
                "Error: Missing required 'config' argument. Please specify --config or set YAMLCRYPT_CONFIG environment variable."
            )
        setattr(namespace, self.dest, Path(values))


class EnvDefaultAgeKey(argparse.Action):
    """Custom argparse Action that defaults to the environment variable AGE_KEY."""

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if values is None:
            values = os.getenv("YAMLCRYPT_AGE_KEY")
        if values is None:
            parser.error(
                "Error: Missing required 'age-key' argument. Please specify --age-key or set YAMLCRYPT_AGE_KEY environment variable."
            )
        setattr(namespace, self.dest, Path(values))


def main():
    parser = argparse.ArgumentParser(
        prog="yamlcrypt", description="Encrypt and decrypt YAML files using page"
    )

    parser.add_argument(
        "--config",
        action=EnvDefaultConfig,
        help="Path to the config.yaml file (can also be set via YAMLCRYPT_CONFIG environment variable)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Encrypt command
    encrypt_parser = subparsers.add_parser("encrypt", help="Encrypt a YAML file")
    encrypt_parser.add_argument("input", type=Path, help="The input YAML file to encrypt")
    group = encrypt_parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--output", type=Path, help="Path to save the encrypted file")
    group.add_argument("--in-place", action="store_true", help="Encrypt the file in place")

    encrypt_parser.set_defaults(func=lambda args: YamlCrypt(args).encrypt())

    # Decrypt command
    decrypt_parser = subparsers.add_parser("decrypt", help="Decrypt a YAML file")
    decrypt_parser.add_argument("input", type=Path, help="The input YAML file to decrypt")
    group = decrypt_parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--output", type=Path, help="Path to save the decrypted file")
    group.add_argument("--in-place", action="store_true", help="Decrypt the file in place")

    decrypt_parser.set_defaults(func=lambda args: YamlCrypt(args).decrypt())

    # Recipients commands
    recipient_parser = subparsers.add_parser("recipient", help="Manage recipient keys")
    recipient_subparsers = recipient_parser.add_subparsers(
        dest="command", help="Recipient Commands"
    )

    recipient_add = recipient_subparsers.add_parser("add", help="Add a key to the config file")
    recipient_add.add_argument(
        "recipient", type=str, help="The name of the recipient in the config file"
    )
    recipient_add.add_argument(
        "--key-file",
        type=Path,
        help="The path of the file where to output the recipient's private key",
    )

    recipient_add.set_defaults(func=lambda args: YamlCrypt(args).recipient_add())

    # Parse arguments
    args = parser.parse_args()

    # Call the assigned function
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
