import numpy as np
import torch
from typing import Tuple


class Image:
    def __init__(self, image: np.ndarray, rotation: Tuple[int, int, int]) -> None:
        self.image = image
        self.rotation = rotation

    def as_cv2(self) -> np.ndarray:
        return self.image

    def as_tensor(self) -> torch.Tensor:
        return torch.from_numpy(np.transpose(self.image, self.rotation))
