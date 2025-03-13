import argparse
import os
from pathlib import Path

from yamlcrypt import __version__
from yamlcrypt.yamlcrypt import YamlCrypt

DEFAULT_CONFIG = ".yamlcrypt.yaml"


class CheckOutputAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, "output", None) and len(values or []) != 1:
            parser.error("When --output is used, input should have exactly one argument.")
        setattr(namespace, self.dest, values)


def main():
    parser = argparse.ArgumentParser(
        prog="yamlcrypt",
        description=f"Encrypt and decrypt YAML files using page ({__version__})",
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=Path(os.getenv("YAMLCRYPT_CONFIG", DEFAULT_CONFIG)),
        help=(
            "Path to the config.yaml file"
            " It can also be set via YAMLCRYPT_CONFIG environment variable"
            " (default: %(default)s)"
        ),
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Encrypt command
    encrypt_parser = subparsers.add_parser("encrypt", help="Encrypt a YAML file")
    encrypt_parser.add_argument(
        "--output",
        type=Path,
        help=("Path to save the encrypted file (When used input should have exactly one value)"),
    )
    encrypt_parser.add_argument(
        "input",
        nargs="+",
        type=Path,
        action=CheckOutputAction,
        help="The input YAML file to encrypt",
    )

    encrypt_parser.set_defaults(func=lambda args: YamlCrypt(args).encrypt())

    # Decrypt command
    decrypt_parser = subparsers.add_parser("decrypt", help="Decrypt a YAML file")
    decrypt_parser.add_argument(
        "--output",
        type=Path,
        help=("Path to save the encrypted file (When used input should have exactly one value)"),
    )
    decrypt_parser.add_argument(
        "input",
        nargs="+",
        action=CheckOutputAction,
        type=Path,
        help="The input YAML file to encrypt",
    )

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
