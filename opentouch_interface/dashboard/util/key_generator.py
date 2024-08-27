class UniqueKeyGenerator:
    """ Class to generate unique keys """

    def __init__(self):
        self._index = 0

    def get_key(self) -> int:
        """ Generate unique key """
        key = self._index
        self._index += 1
        return key
