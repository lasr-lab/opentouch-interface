import importlib

import numpy as np
from typing import Tuple


class Image:
    def __init__(self, image: np.ndarray, rotation: Tuple[int, int, int]) -> None:
        self._image: np.ndarray = image
        self._rotation: Tuple[int, int, int] = rotation

    def as_cv2(self) -> np.ndarray:
        return self._image

    def as_tensor(self):
        try:
            torch = importlib.import_module('torch')
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "The 'torch' library is not installed. Please install it using 'pip install torch'."
            )

        return torch.from_numpy(np.transpose(self._image, self._rotation))
