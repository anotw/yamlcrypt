from yamlcrypt.config import YamlCryptConfig
from yamlcrypt.errors import YamlCryptConfigNotFoundError, YamlCryptError
from yamlcrypt.logger import logger
from yamlcrypt.processor import YamlCryptProcessor, YamlCryptProcessorArgs


class YamlCrypt:
    def __init__(self, args):
        self.args = args
        self.log = logger()
        self._config = None
        if self.args.output and len(self.args.input) != 1:
            raise YamlCryptError("When --output is used, input should have exactly one argument.")

    @property
    def config(self):
        if not self._config:
            self._config = YamlCryptConfig(self.log).load(path=self.args.config)
        return self._config

    def processors(self):
        for input in self.args.input:
            yield YamlCryptProcessor(
                args=YamlCryptProcessorArgs(input=input, output=self.args.output),
                config=self.config,
            )

    def encrypt(self):
        for processor in self.processors():
            processor.encrypt()

    def decrypt(self):
        for processor in self.processors():
            processor.decrypt()

    def recipient_add(self):
        # Create config file without loading so we can catch the error
        self._config = YamlCryptConfig(log=self.log)
        try:
            self.config.load(path=self.args.config)
        except YamlCryptConfigNotFoundError:
            self.log.info(
                f"Config file does not exist yet, it will be created ({self.args.config})"
            )

        self.config.add_recipient(self.args.recipient)
        recipients = {}
        if self.args.key_file:
            recipients[self.args.recipient] = self.args.key_file
        self.config.save(path=self.args.config, recipients=recipients)
