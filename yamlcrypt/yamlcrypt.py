from yamlcrypt.config import YamlCryptConfig
from yamlcrypt.errors import YamlCryptConfigNotFoundError
from yamlcrypt.logger import logger
from yamlcrypt.processor import YamlCryptProcessor, YamlCryptProcessorArgs
from yamlcrypt.utils import namespace_to_dataclass


class YamlCrypt:
    def __init__(self, args):
        self.args = args
        self.log = logger()
        self._config = None
        self._processor = None

    @property
    def config(self):
        if not self._config:
            self._config = YamlCryptConfig(self.log).load(path=self.args.config)
        return self._config

    @property
    def processor(self):
        if not self._processor:
            self._processor = YamlCryptProcessor(
                args=namespace_to_dataclass(self.args, YamlCryptProcessorArgs), config=self.config
            )
        return self._processor

    def encrypt(self):
        self.processor.encrypt()

    def decrypt(self):
        self.processor.decrypt()

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
