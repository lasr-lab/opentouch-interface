import threading
import datetime
from typing import Union, List, Self

import h5py

from opentouch_interface.interface.dataclasses.image.image import Image


class ImageWriter:
    _file_lock: threading.Lock = threading.Lock()  # Class-level lock

    def __init__(self, file_path: str, sensor_name: str, config: str):
        self.file_path: str = file_path
        self.sensor_name: str = sensor_name
        self.config: str = config

        self.frames_buffer: List[Image] = []

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._save_buffer_to_file()

    @staticmethod
    def write_attr(file_path: str, attribute: str, value: Union[int, float, bool, str, None]) -> None:
        """ Writes an attributes to a file. """

        with ImageWriter._file_lock:
            with h5py.File(file_path, 'a') as hf:
                hf.attrs[attribute] = "" if value is None else value

    def save_to_buffer(self, image: Image) -> None:
        self.frames_buffer.append(image)

    def _save_buffer_to_file(self) -> None:
        if not self.frames_buffer:
            return

        with ImageWriter._file_lock:  # Ensure exclusive access
            with h5py.File(self.file_path, 'a') as hf:

                # Save general metadata for that .touch file
                hf.attrs['last-edited'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                hf.attrs['version'] = 1

                # Save sensor-specific information (config and data)
                if self.sensor_name not in hf:
                    group = hf.create_group(self.sensor_name)
                    group.attrs['config'] = self.config

                # Save image data
                frame_count: int = 0
                for image in self.frames_buffer:
                    dataset_name: str = f'image_{frame_count:06d}_cv2'
                    group.create_dataset(dataset_name, data=image.as_cv2())
                    frame_count += 1

            self.frames_buffer = []
