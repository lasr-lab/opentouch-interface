import ast
import datetime
from io import BytesIO
import threading

import numpy as np
import h5py
import torch
from typing import Tuple, List, Optional, Union, Dict


class Image:
    def __init__(self, image: np.ndarray, rotation: Tuple[int, int, int]) -> None:
        self.image = image
        self.rotation = rotation

    def as_cv2(self) -> np.ndarray:
        return self.image

    def as_tensor(self) -> torch.Tensor:
        return torch.from_numpy(np.transpose(self.image, self.rotation))


class ImageWriter:
    _file_lock = threading.Lock()  # Class-level lock

    def __init__(self, file_path: str, sensor_name: str, config: dict):
        self.file_path = file_path
        self.frames_buffer = []
        self.config = config
        self.total_frames = self._get_total_frames(sensor_name)
        self.sensor_name = sensor_name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._save_buffer_to_file()

    def save(self, image: Image):
        self.frames_buffer.append(image)

    def _get_total_frames(self, sensor_name: str) -> int:
        try:
            with h5py.File(self.file_path, 'r') as hf:
                if sensor_name in hf:
                    return len(hf[sensor_name].keys())
                return 0
        except FileNotFoundError:
            return 0

    def _save_buffer_to_file(self):
        if not self.frames_buffer:
            return

        with ImageWriter._file_lock:  # Ensure exclusive access
            with h5py.File(self.file_path, 'a') as hf:

                # Save general metadata for that .h5 file
                hf.attrs['last-edited'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                hf.attrs['version'] = 1

                # Save sensor-specific information (config and data)
                if self.sensor_name not in hf:
                    group = hf.create_group(self.sensor_name)
                    group.attrs['config'] = str(self.config)
                else:
                    group = hf[self.sensor_name]

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

        self.frames: Dict[str, List[Image]] = self._load_frames()
        self.current_index = {sensor_name: 0 for sensor_name in self.frames}
        self.fps = self._read_fps()

    def _read_fps(self) -> int:
        with self._open_file() as hf:
            return hf.attrs.get('fps', 30)  # Read FPS from file, default to 30 if not found

    def _open_file(self):
        if self.file_path:
            return h5py.File(self.file_path, 'r')
        else:
            return h5py.File(self.file, 'r')

    def _load_frames(self) -> Dict[str, List[Image]]:
        sensor_images = {}
        with self._open_file() as hf:
            for sensor_name in hf.keys():
                if isinstance(hf[sensor_name], h5py.Group):
                    images = []
                    group = hf[sensor_name]
                    for key in group.keys():
                        if key.startswith('image_') and key.endswith('_cv2'):
                            img_data = group[key][()]
                            images.append(Image(img_data, (0, 1, 2)))
                    if images:  # Only add to a dictionary if images were found
                        sensor_images[sensor_name] = images

        self.current_index = 0  # Reset index after reading all images
        return sensor_images

    def get_all_frames(self, sensor_name: str) -> List[Image]:
        return self.frames[sensor_name]

    def get_next_frame(self, sensor_name: str) -> Optional[Image]:
        if self.current_index[sensor_name] < len(self.frames[sensor_name]):
            next_image = self.frames[sensor_name][self.current_index[sensor_name]]
            self.current_index[sensor_name] += 1
            return next_image
        else:
            return self._get_black_image()

    def restart(self, sensor_name: str) -> None:
        """Jump back to the beginning of the frames."""
        self.current_index[sensor_name] = 0

    def jump_to(self, sensor_name: str, percentage: float) -> None:
        """Jump to a position specified by the percentage of the total frames."""
        if not (0.0 <= percentage <= 1.0):
            raise ValueError("Percentage must be between 0.0 and 1.0")

        self.current_index[sensor_name] = int(percentage * len(self.frames))

    def get_progress(self, sensor_name: str) -> float:
        """Retrieve the current position as a percentage between 0 and 1."""
        if len(self.frames) == 0:
            return 0.0
        return self.current_index[sensor_name] / len(self.frames[sensor_name])

    def _get_black_image(self) -> Image:
        # Create a black image of the same dimensions as the last read image
        if self.frames:
            last_image = self.frames[next(iter(self.frames))][-1]
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
