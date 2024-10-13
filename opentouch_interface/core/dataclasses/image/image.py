import importlib
import numpy as np
from typing import Tuple


class Image:
    """
    A class to represent an image with a specified rotation.

    :param image: The image as a NumPy array.
    :type image: np.ndarray
    :param rotation: A tuple defining the rotation axes.
    :type rotation: Tuple[int, int, int]
    """
    def __init__(self, image: np.ndarray, rotation: Tuple[int, int, int]) -> None:
        self._image: np.ndarray = image
        self._rotation: Tuple[int, int, int] = rotation

    def as_cv2(self) -> np.ndarray:
        """
        Returns the image in its original NumPy array form, typically used for OpenCV.

        :returns: The image as a NumPy array.
        :rtype: np.ndarray
        """
        return self._image

    def as_tensor(self):
        """
        Converts the image to a PyTorch tensor, applying the specified rotation.

        :raises ModuleNotFoundError: If the 'torch' library is not installed.
        :returns: The image as a PyTorch tensor.
        """
        try:
            torch = importlib.import_module('torch')
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "The 'torch' library is not installed. Please install it using 'pip install torch'."
            )

        return torch.from_numpy(np.transpose(self._image, self._rotation))
