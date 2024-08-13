import ast
from io import BytesIO
from typing import Union, List, Optional

import h5py
import numpy as np

from opentouch_interface.interface.dataclasses.image.image import Image


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

    def get_sensor_names(self) -> List[str]:
        with self._open_file() as hf:
            # List top-level groups, which represent sensors
            return list(hf.keys())

    def get_payload(self):
        with self._open_file() as hf:
            payload = hf.attrs['payload']
            return ast.literal_eval(payload)
