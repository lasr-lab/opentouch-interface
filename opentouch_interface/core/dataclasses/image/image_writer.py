import threading
import datetime
from typing import Union, List
import h5py
from opentouch_interface.core.dataclasses.image.image import Image


class ImageWriter:
    """
    A class to manage writing image data to an HDF5 file, supporting buffered writes and thread-safe file access.

    :param file_path: Path to the HDF5 file where data will be written.
    :type file_path: str
    :param sensor_name: Name of the sensor used for recording the images.
    :type sensor_name: str
    :param config: Configuration string related to the sensor settings.
    :type config: str
    """
    _file_lock: threading.Lock = threading.Lock()  # Class-level lock for thread safety

    def __init__(self, file_path: str, sensor_name: str, config: str):
        self.file_path: str = file_path
        self.sensor_name: str = sensor_name
        self.config: str = config
        self.frames_buffer: List[Image] = []

    def __enter__(self):
        """
        Enter the runtime context related to this object. Used for 'with' statement support.

        :returns: The `ImageWriter` instance itself.
        :rtype: ImageWriter
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the runtime context, ensuring that the buffer is saved to the file upon exiting.
        """
        self._save_buffer_to_file()

    @staticmethod
    def write_attr(file_path: str, attribute: str, value: Union[int, float, bool, str, None]) -> None:
        """
        Writes an attribute to the HDF5 file in a thread-safe manner.

        :param file_path: Path to the HDF5 file.
        :type file_path: str
        :param attribute: The name of the attribute to write.
        :type attribute: str
        :param value: The value to set for the attribute (supports int, float, bool, str, or None).
        :type value: Union[int, float, bool, str, None]
        """
        with ImageWriter._file_lock:
            with h5py.File(file_path, 'a') as hf:
                hf.attrs[attribute] = "" if value is None else value

    def save_to_buffer(self, image: Image) -> None:
        """
        Adds an image to the buffer for later writing to the file.

        :param image: The image to buffer.
        :type image: Image
        """
        self.frames_buffer.append(image)

    def _save_buffer_to_file(self) -> None:
        """
        Saves all images in the buffer to the HDF5 file. Clears the buffer after saving.
        This method ensures thread-safe access to the file during the write operation.
        """
        if not self.frames_buffer:
            return

        with ImageWriter._file_lock:  # Ensure exclusive access
            with h5py.File(self.file_path, 'a') as hf:
                # Save general metadata for the HDF5 file
                hf.attrs['last-edited'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                hf.attrs['version'] = 1

                # Save sensor-specific information (config and data)
                if self.sensor_name not in hf:
                    group = hf.create_group(self.sensor_name)
                    group.attrs['config'] = self.config

                # Save each image in the buffer to the file as a dataset
                frame_count: int = 0
                for image in self.frames_buffer:
                    dataset_name: str = f'image_{frame_count:06d}_cv2'
                    group.create_dataset(dataset_name, data=image.as_cv2())
                    frame_count += 1

            self.frames_buffer = []  # Clear the buffer after saving
