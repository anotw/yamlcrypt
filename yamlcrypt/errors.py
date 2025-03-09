class YamlCryptError(Exception):
    pass


class YamlCryptConfigNotFoundError(YamlCryptError):
    pass


class YamlCryptDuplicateIdentify(YamlCryptError):
    pass
