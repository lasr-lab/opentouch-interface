import os
import re
import threading
import time
import warnings
from typing import Any, Optional, Dict, List

import cv2
import numpy as np

from opentouch_interface.interface.dataclasses.buffer import CentralBuffer
from opentouch_interface.interface.dataclasses.image.image import Image
from opentouch_interface.interface.dataclasses.image.image_writer import ImageWriter
from opentouch_interface.interface.dataclasses.validation.sensors.gelsight_config import GelsightConfig
from opentouch_interface.interface.options import SensorSettings, DataStream
from opentouch_interface.interface.touch_sensor import TouchSensor


class GelsightMiniCamera:
    def __init__(self):
        self._dev_id: Optional[int] = None
        self._camera: Optional[cv2.VideoCapture] = None

    def connect(self) -> None:
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

    def disconnect(self):
        self._camera.release()


class GelsightMiniSensor(TouchSensor):

    def __init__(self, config: GelsightConfig):
        super().__init__(config=config)
        self.central_buffer: CentralBuffer = CentralBuffer()

        self.reading_thread: Optional[threading.Thread] = None
        self.recording_thread: Optional[threading.Thread] = None
        self.stop_event: threading.Event = threading.Event()
        self.recording_event: threading.Event = threading.Event()

    def initialize(self) -> None:
        # Can't find multiple connected Gelsight sensors
        self.sensor = GelsightMiniCamera()

    def connect(self) -> None:
        self.sensor.connect()

        # Start the reading thread
        self.start_reading()

    def set(self, attr: SensorSettings, value: Any = None) -> Any:
        warnings.warn("The GelsightMini sensor does not support setting a value.", stacklevel=2)

    def get(self, attr: SensorSettings) -> Any:
        if not isinstance(attr, SensorSettings):
            raise TypeError(f"Expected attr to be of type SensorSettings but found {type(attr)} instead")
        return getattr(self.config, attr.name.lower(), None)

    def read(self, attr: DataStream, value: Any = None) -> Optional[Image]:
        if not isinstance(attr, DataStream):
            raise TypeError(f"Expected attr to be of type DataStream but found {type(attr)} instead")

        if attr == DataStream.FRAME:
            return self.central_buffer.get()
        else:
            warnings.warn(f"The provided attribute '{attr}' did not match any available attribute. "
                          f"Returning None.", stacklevel=2)
            return None

    def show(self, attr: DataStream):
        if not isinstance(attr, DataStream):
            raise TypeError(f"Expected attr to be of type DataStream but found {type(attr)} instead")

        if attr == DataStream.FRAME:
            while not self.stop_event.is_set():
                image = self.read(attr=DataStream.FRAME)
                if image is not None:
                    cv2.imshow('Digit view', image.as_cv2())
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.stop_event.set()
                    break

            cv2.destroyAllWindows()
        else:
            warnings.warn(f"The provided attribute '{attr}' did not match any available attribute.",
                          stacklevel=2)

    def calibrate(self, num_frames: int = 100, skip_frames: int = 20) -> Optional[Image]:
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

    def disconnect(self):
        self.stop_event.set()
        self.recording_event.set()
        if self.reading_thread:
            self.reading_thread.join()
        if self.recording_thread:
            self.recording_thread.join()

        self.sensor.disconnect()

    def start_reading(self):
        """Start reading data from the sensor at the configured sampling frequency."""

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

    def start_recording(self):
        """Start recording data from the central buffer at the configured sampling frequency."""
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

    def stop_recording(self):
        """Stop the ongoing recording."""
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_event.set()
            self.recording_thread.join()
            self.recording_thread = None

        self.recording = False

    def _to_filtered_dict(self) -> Dict:
        """Returns a dictionary with specific attribute-value pairs."""
        include_keys: List[str] = [
            'sensor_name', 'sensor_type', 'sampling_frequency', 'recording_frequency'
        ]
        data: Dict = self.config.dict()
        filtered_data: Dict = {key: value for key, value in data.items() if key in include_keys}
        return filtered_data
