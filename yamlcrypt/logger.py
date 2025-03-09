from types import SimpleNamespace

from yamlpath.wrappers import ConsolePrinter


def logger(quiet=False, verbose=False, debug=False) -> ConsolePrinter:
    return ConsolePrinter(SimpleNamespace(quiet=quiet, verbose=verbose, debug=debug))


class DelayedLogger:
    def __init__(self, logger):
        self.logger = logger
        self.messages = []

    def dump(self):
        for fct, message, args in self.messages:
            if args:
                fct(message, **args)
            else:
                fct(message)

    def info(self, message):
        self.messages.append((self.logger.info, message, None))

    def verbose(self, message):
        self.messages.append((self.logger.verbose, message, None))

    def warning(self, message):
        self.messages.append((self.logger.warning, message, None))

    def error(self, message, exit_code=None):
        self.messages.append((self.logger.error, message, {"exit_code": exit_code}))

    def critical(self, message, exit_code=1):
        self.messages.append((self.logger.error, message, {"exit_code": exit_code}))

    def debug(self, message, **kwargs):
        self.messages.append((self.logger.error, message, kwargs))
