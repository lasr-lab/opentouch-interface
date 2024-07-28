import time
from io import BytesIO

import numpy as np
import h5py
import torch
from typing import Tuple, List, Optional, Union


class Image:
    def __init__(self, image: np.ndarray, rotation: Tuple[int, int, int]) -> None:
        self.image = image
        self.rotation = rotation

    def as_cv2(self) -> np.ndarray:
        return self.image

    def as_tensor(self) -> torch.Tensor:
        return torch.from_numpy(np.transpose(self.image, self.rotation))


class ImageWriter:
    def __init__(self, file_path: str, fps: int):
        self.file_path = file_path
        self.frames_buffer = []
        self.fps = fps
        self.total_frames = self._get_total_frames()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._save_buffer_to_file()

    def save(self, image: Image):
        self.frames_buffer.append(image)

    def _get_total_frames(self) -> int:
        try:
            with h5py.File(self.file_path, 'r') as hf:
                if 'frames' in hf:
                    return len(hf['frames'].keys())
                return 0
        except FileNotFoundError:
            return 0

    def _save_buffer_to_file(self):
        if not self.frames_buffer:
            return

        with h5py.File(self.file_path, 'a') as hf:
            if 'frames' not in hf:
                group = hf.create_group('frames')
                hf.attrs['fps'] = self.fps  # Save FPS as an attribute of the file
            else:
                group = hf['frames']

            for image in self.frames_buffer:
                dataset_name = f'image_{self.total_frames:06d}_cv2'
                group.create_dataset(dataset_name, data=image.as_cv2())
                self.total_frames += 1

        self.frames_buffer = []


class ImageReader:
    def __init__(self, file: Union[BytesIO, None] = None, path: Union[str, None] = None):
        # Check that exactly one of file or path is provided
        if (file is None and path is None) or (file is not None and path is not None):
            raise ValueError('Exactly one of file or path must be provided.')

        if file is not None:
            if not isinstance(file, BytesIO):
                raise TypeError('File must be of type BytesIO.')
            self.file_path = None
            self.file = file
        else:
            if not isinstance(path, str):
                raise TypeError('Path must be of type str.')
            self.file_path = path
            self.file = None
            if not self.file_path.endswith('.h5'):
                raise ValueError('Path must end with ".h5".')

        self.frames = []
        self.current_index = 0
        self.fps = self._read_fps()
        self._load_frames()
        self.last_frame_time = 0  # Timestamp of the last frame read
        self.last_frame = None  # Last frame that was read

    def _read_fps(self) -> int:
        with self._open_file() as hf:
            return hf.attrs.get('fps', 30)  # Read FPS from file, default to 30 if not found

    def _open_file(self):
        if self.file_path:
            return h5py.File(self.file_path, 'r')
        else:
            return h5py.File(self.file, 'r')

    def _load_frames(self) -> List[Image]:
        images = []
        with self._open_file() as hf:
            if 'frames' in hf:
                group = hf['frames']
                for key in group.keys():
                    if key.startswith('image_') and key.endswith('_cv2'):
                        img_data = group[key][()]
                        images.append(Image(img_data, (0, 1, 2)))

        self.frames = images
        self.current_index = 0  # Reset index after reading all images
        return images

    def get_all_frames(self) -> List[Image]:
        return self.frames

    def get_next_frame(self) -> Optional[Image]:
        if self.current_index < len(self.frames):
            next_image = self.frames[self.current_index]
            self.current_index += 1
            return next_image
        else:
            return self._get_black_image()

    def restart(self) -> None:
        """Jump back to the beginning of the frames."""
        self.current_index = 0
        self.last_frame_time = 0
        self.last_frame = None

    def jump_to(self, percentage: float) -> None:
        """Jump to a position specified by the percentage of the total frames."""
        if not (0.0 <= percentage <= 1.0):
            raise ValueError("Percentage must be between 0.0 and 1.0")

        self.current_index = int(percentage * len(self.frames))
        self.last_frame_time = 0
        self.last_frame = None

    def get_progress(self) -> float:
        """Retrieve the current position as a percentage between 0 and 1."""
        if len(self.frames) == 0:
            return 0.0
        return self.current_index / len(self.frames)

    def _get_black_image(self) -> Image:
        # Create a black image of the same dimensions as the last read image
        if self.frames:
            last_image = self.frames[-1]
            black_image = np.zeros_like(last_image.as_cv2())
            return Image(black_image, (0, 1, 2))
        else:
            # If no images were read at all, return a default-sized black image
            default_size = (640, 480, 3)  # Example default size
            black_image = np.zeros(default_size, dtype=np.uint8)
            return Image(black_image, (0, 1, 2))
