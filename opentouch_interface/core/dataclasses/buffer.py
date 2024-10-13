import threading
from opentouch_interface.core.dataclasses.image.image import Image


class CentralBuffer:
    """
    A thread-safe buffer class for storing and retrieving a single `Image` object.

    This class ensures that access to the buffer is synchronized using a lock,
    allowing safe use across multiple threads.

    """
    def __init__(self):
        """
        Initializes the `CentralBuffer` with a `None` buffer and a threading lock to
        ensure thread safety during data access.
        """
        self.buffer = None
        self.lock = threading.Lock()

    def put(self, data: Image) -> None:
        """
        Safely stores the given `Image` in the buffer, replacing any existing data.

        :param data: The image to store in the buffer.
        :type data: Image
        """
        with self.lock:
            self.buffer = data

    def get(self) -> Image:
        """
        Safely retrieves the `Image` from the buffer. Returns `None` if the buffer is empty.

        :returns: The image stored in the buffer, or `None` if no image is present.
        :rtype: Image
        """
        with self.lock:
            return self.buffer
