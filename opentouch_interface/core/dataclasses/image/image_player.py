from typing import List
import numpy as np
from opentouch_interface.core.dataclasses.image.image import Image


class ImagePlayer:
    """
    A class to play through a sequence of image frames, controlling the playback speed.

    :param frames: A list of `Image` objects to be played.
    :type frames: List[Image]
    :param fps: Frames per second, controls the playback speed.
    :type fps: int
    """
    def __init__(self, frames: List[Image], fps: int):
        self.frames: List[Image] = frames
        self.fps: int = fps
        self._current_index: int = 0

    def next_frame(self) -> Image:
        """
        Returns the next frame in the sequence. If there are no more frames, returns a black image.

        :returns: The next `Image` in the sequence or a black image if at the end.
        :rtype: Image
        """
        if self._current_index < len(self.frames):
            frame = self.frames[self._current_index]
            self._current_index += 1
            return frame
        return self._get_black_image()

    def restart(self) -> None:
        """
        Resets the player to the beginning of the sequence.
        """
        self._current_index = 0

    def _get_black_image(self) -> Image:
        """
        Returns a black image with the same dimensions as the last frame, or a default size if no frames exist.

        :returns: A black `Image` object.
        :rtype: Image
        """
        if self.frames:
            last_image = self.frames[-1]
            black_image = np.zeros_like(last_image.as_cv2())
        else:
            default_size = (640, 480, 3)  # Default to 640x480 resolution with 3 color channels
            black_image = np.zeros(default_size, dtype=np.uint8)

        return Image(black_image, (0, 1, 2))
