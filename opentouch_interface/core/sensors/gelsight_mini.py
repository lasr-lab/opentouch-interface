import os
import re
import threading
import time
import warnings
from typing import Any, Optional, Dict, List

import cv2
import numpy as np

from opentouch_interface.core.dataclasses.buffer import CentralBuffer
from opentouch_interface.core.dataclasses.image.image import Image
from opentouch_interface.core.dataclasses.image.image_writer import ImageWriter
from opentouch_interface.core.validation.gelsight_config import GelsightConfig
from opentouch_interface.core.dataclasses.options import SensorSettings, DataStream
from opentouch_interface.core.sensors.touch_sensor import TouchSensor


class GelsightMiniCamera:
    """
    A class to interface with the GelSight Mini camera.

    This class handles the connection, image capture, and disconnection for the GelSight Mini sensor.
    """

    def __init__(self):
        self._dev_id: Optional[int] = None
        self._camera: Optional[cv2.VideoCapture] = None

    def connect(self) -> None:
        """Attempts to find and connect to the GelSight Mini camera by searching the video devices."""
        for file in os.listdir("/sys/class/video4linux"):
            real_file = os.path.join("/sys/class/video4linux", file, "name")
            with open(real_file, "rt") as name_file:
                name = name_file.read().strip()

            if 'GelSight Mini' in name:
                self._dev_id = int(re.search(r"\d+$", file).group())

        self._camera = cv2.VideoCapture(self._dev_id)
        if not self._camera or not self._camera.isOpened():
            warnings.warn("Failed to open GelSight Mini camera device")

    def get_image(self) -> Optional[np.ndarray]:
        """
        Captures an image from the camera, crops it, and resizes it to 320x240.

        :returns: The processed frame as a NumPy array, or None if the capture fails.
        :rtype: Optional[np.ndarray]
        """
        if self._camera:
            ret, frame = self._camera.read()
            if ret and frame is not None:
                # Remove 1/7th of the border from each side
                size_x = int(frame.shape[0] * (1 / 7))
                size_y = int(frame.shape[1] * (1 / 7))

                # Crop the image
                cropped_frame = frame[size_x + 2:frame.shape[0] - size_x, size_y:frame.shape[1] - size_y]

                # Resize the image to 320x240
                resized_frame = cv2.resize(cropped_frame, (320, 240))

                return resized_frame
        return None

    def disconnect(self) -> None:
        """Releases the camera resource when done."""
        if self._camera:
            self._camera.release()


class GelsightMiniSensor(TouchSensor):
    """
    A class representing a GelSight Mini sensor, inheriting from `TouchSensor`.

    This class manages connecting to the GelSight Mini, reading frames, and managing
    recording sessions.

    :param config: The configuration object that contains the sensor settings.
    :type config: GelsightConfig
    """

    def __init__(self, config: GelsightConfig):
        super().__init__(config=config)
        self.central_buffer: CentralBuffer = CentralBuffer()

        self.reading_thread: Optional[threading.Thread] = None
        self.recording_thread: Optional[threading.Thread] = None
        self.stop_event: threading.Event = threading.Event()
        self.recording_event: threading.Event = threading.Event()

    def initialize(self) -> None:
        """Initializes the sensor by creating a GelSight Mini camera object."""
        self.sensor = GelsightMiniCamera()

    def connect(self) -> None:
        """Connects to the GelSight Mini sensor and starts the reading thread."""
        self.sensor.connect()

        # Start the reading thread
        self.start_reading()

    def set(self, attr: SensorSettings, value: Any = None) -> Any:
        """
        The GelSight Mini sensor does not support setting any sensor values.

        :param attr: The sensor attribute to set (not supported).
        :type attr: SensorSettings
        :param value: The value to set (not supported).
        :type value: Any
        :raises Warning: Always warns because no attributes can be set.
        """
        warnings.warn("The GelsightMini sensor does not support setting a value.", stacklevel=2)

    def get(self, attr: SensorSettings) -> Any:
        """
        Retrieves the value of a sensor setting from the configuration.

        :param attr: The sensor setting to retrieve.
        :type attr: SensorSettings
        :returns: The value of the specified setting.
        :rtype: Any
        :raises TypeError: If an unsupported attribute is passed.
        """
        if not isinstance(attr, SensorSettings):
            raise TypeError(f"Expected attr to be of type SensorSettings but found {type(attr)} instead")
        return getattr(self.config, attr.name.lower(), None)

    def read(self, attr: DataStream, value: Any = None) -> Optional[Image]:
        """
        Reads a frame from the central buffer, if available.

        :param attr: The data stream to read (must be `FRAME`).
        :type attr: DataStream
        :param value: Unused, reserved for future use.
        :type value: Any
        :returns: The image from the buffer, or None if unavailable.
        :rtype: Optional[Image]
        :raises TypeError: If an unsupported data stream is passed.
        """
        if not isinstance(attr, DataStream):
            raise TypeError(f"Expected attr to be of type DataStream but found {type(attr)} instead")

        if attr == DataStream.FRAME:
            return self.central_buffer.get()
        else:
            warnings.warn(f"The provided attribute '{attr}' did not match any available attribute. "
                          f"Returning None.", stacklevel=2)
            return None

    def show(self, attr: DataStream) -> None:
        """
        Displays the frames in a window as they are read.

        :param attr: The data stream to display (must be `FRAME`).
        :type attr: DataStream
        :raises TypeError: If an unsupported data stream is passed.
        """
        if not isinstance(attr, DataStream):
            raise TypeError(f"Expected attr to be of type DataStream but found {type(attr)} instead")

        if attr == DataStream.FRAME:
            while not self.stop_event.is_set():
                image = self.read(attr=DataStream.FRAME)
                if image is not None:
                    cv2.imshow('GelSight view', image.as_cv2())
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.stop_event.set()
                    break

            cv2.destroyAllWindows()
        else:
            warnings.warn(f"The provided attribute '{attr}' did not match any available attribute.", stacklevel=2)

    def calibrate(self, num_frames: int = 100, skip_frames: int = 20) -> Optional[Image]:
        """
        Calibrates the sensor by averaging a series of frames.

        :param num_frames: The number of frames to capture for calibration.
        :type num_frames: int
        :param skip_frames: The number of initial frames to skip before capturing.
        :type skip_frames: int
        :returns: The averaged calibration image.
        :rtype: Optional[Image]
        """
        interval: float = 1.0 / self.config.sampling_frequency

        # Skip the initial frames
        skipped: int = 0
        while skipped < skip_frames:
            image = self.read(attr=DataStream.FRAME)
            if image is not None:
                skipped += 1
            time.sleep(interval)

        # Collect frames after skipping
        frames = []
        collected = 0
        while collected < num_frames:
            image = self.read(attr=DataStream.FRAME)
            if image is not None:
                frames.append(image.as_cv2())
                collected += 1
            time.sleep(interval)

        # Calculate the average frame
        average_frame = np.mean(frames, axis=0).astype(np.uint8)
        average_image = Image(image=average_frame, rotation=(0, 1, 2))

        self.config._calibration = average_image
        return average_image

    def disconnect(self) -> None:
        """Stops any ongoing threads and disconnects the sensor."""
        self.stop_event.set()
        self.recording_event.set()
        if self.reading_thread:
            self.reading_thread.join()
        if self.recording_thread:
            self.recording_thread.join()

        self.sensor.disconnect()

    def start_reading(self) -> None:
        """Starts reading data from the sensor in a separate thread."""

        def read_sensor():
            interval = 1.0 / self.config.sampling_frequency
            while not self.stop_event.is_set():
                start_time = time.time()
                try:
                    frame = self.sensor.get_image()
                    if frame is not None:
                        image = Image(image=frame, rotation=(0, 1, 2))
                        self.central_buffer.put(image)
                except Exception as e:
                    print(e)
                elapsed_time = time.time() - start_time
                time_to_sleep = interval - elapsed_time
                if time_to_sleep > 0:
                    time.sleep(time_to_sleep)

        self.reading_thread = threading.Thread(target=read_sensor)
        self.reading_thread.start()

    def start_recording(self) -> None:
        """Starts recording frames from the central buffer to a file."""
        if self.recording_thread and self.recording_thread.is_alive():
            return

        # Clear the event to allow the new recording session to start
        self.recording_event.clear()

        def record_data():
            interval = 1.0 / self.config.recording_frequency
            with ImageWriter(file_path=self.path, sensor_name=self.config.sensor_name,
                             config=str(self._to_filtered_dict())) as recorder:
                while not self.recording_event.is_set():
                    start_time = time.time()
                    image = self.read(attr=DataStream.FRAME)
                    if image:
                        recorder.save_to_buffer(image)
                    elapsed_time = time.time() - start_time
                    time_to_sleep = interval - elapsed_time
                    if time_to_sleep > 0:
                        time.sleep(time_to_sleep)

        self.recording_thread = threading.Thread(target=record_data)
        self.recording_thread.start()
        self.recording = True

    def stop_recording(self) -> None:
        """Stops the ongoing recording session."""
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_event.set()
            self.recording_thread.join()
            self.recording_thread = None

        self.recording = False

    def _to_filtered_dict(self) -> Dict:
        """
        Returns a dictionary containing specific attributes to be saved during recording.

        :returns: A dictionary with sensor configuration attributes.
        :rtype: Dict
        """
        include_keys: List[str] = [
            'sensor_name', 'sensor_type', 'sampling_frequency', 'recording_frequency'
        ]
        data: Dict = self.config.dict()
        filtered_data: Dict = {key: value for key, value in data.items() if key in include_keys}
        return filtered_data
