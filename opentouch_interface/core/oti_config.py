class OTIConfig:
    _base_directory = './datasets'

    @classmethod
    def set_base_directory(cls, base_directory):
        cls._base_directory = base_directory

    @classmethod
    def get_base_directory(cls):
        return cls._base_directory
