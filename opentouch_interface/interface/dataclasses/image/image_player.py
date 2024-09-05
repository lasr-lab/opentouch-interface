from typing import List

import numpy as np

from opentouch_interface.interface.dataclasses.image.image import Image


class ImagePlayer:
    def __init__(self, frames: List[Image], fps: int):
        self.frames: List[Image] = frames
        self.fps: int = fps

        self._current_index: int = 0

    def next_frame(self) -> Image:
        if self._current_index < len(self.frames):
            frame = self.frames[self._current_index]
            self._current_index += 1
            return frame
        return self._get_black_image()

    def restart(self) -> None:
        """Jump back to the beginning of the frames."""
        self._current_index = 0

    def _get_black_image(self) -> Image:
        if self.frames:
            last_image = self.frames[-1]
            black_image = np.zeros_like(last_image.as_cv2())
        else:
            default_size = (640, 480, 3)  # Example default size
            black_image = np.zeros(default_size, dtype=np.uint8)

        return Image(black_image, (0, 1, 2))
