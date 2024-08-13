import threading

from opentouch_interface.interface.dataclasses.image.image import Image


class CentralBuffer:
    def __init__(self):
        self.buffer = None
        self.lock = threading.Lock()

    def put(self, data: Image):
        with self.lock:
            self.buffer = data

    def get(self) -> Image:
        with self.lock:
            return self.buffer
