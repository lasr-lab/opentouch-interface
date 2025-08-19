class UniqueKeyGenerator:
    """
    A class to generate unique integer keys sequentially starting from 0.

    Each time `get_key` is called, it returns a new unique integer and increments the internal counter.
    """

    def __init__(self):
        """
        Initializes the UniqueKeyGenerator with an internal counter starting at 0.
        """
        self._index = 0

    def get_key(self) -> int:
        """
        Generates and returns the next unique integer key.

        :return: A unique integer key, starting from 0 and incrementing by 1 with each call.
        :rtype: int
        """
        key = self._index
        self._index += 1
        return key
