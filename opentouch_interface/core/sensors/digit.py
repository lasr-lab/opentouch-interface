import threading
import time
from typing import Any, Dict, Optional, List
import warnings
import cv2
import numpy as np

from opentouch_interface.core.dataclasses.buffer import CentralBuffer
from opentouch_interface.core.dataclasses.image.image_writer import ImageWriter
from opentouch_interface.core.validation.digit_config import DigitConfig
from opentouch_interface.core.dataclasses.options import SensorSettings, DataStream
from opentouch_interface.core.sensors.touch_sensor import TouchSensor
from opentouch_interface.core.dataclasses.image.image import Image
from digit_interface.digit import Digit


class DigitSensor(TouchSensor):
    """
    A class representing a Digit touch sensor, inheriting from TouchSensor. This class
    manages the connection, configuration, reading, and recording of data from a Digit sensor.

    :param config: The configuration object that contains sensor settings.
    :type config: DigitConfig
    """

    def __init__(self, config: DigitConfig):
        super().__init__(config=config)
        self.central_buffer: CentralBuffer = CentralBuffer()

        self.reading_thread: Optional[threading.Thread] = None
        self.recording_thread: Optional[threading.Thread] = None
        self.stop_event: threading.Event = threading.Event()
        self.recording_event: threading.Event = threading.Event()

    def initialize(self) -> None:
        """Initializes the Digit sensor using the provided configuration."""
        self.sensor = Digit(serial=self.config.serial_id, name=self.config.sensor_name)

    def connect(self) -> None:
        """
        Connects to the Digit sensor and configures it based on the provided settings.
        Starts the sensor reading thread.
        """
        self.sensor.connect()
        self.set(SensorSettings.RESOLUTION, self.config.resolution)
        self.set(SensorSettings.FPS, self.config.fps)
        self.set(SensorSettings.INTENSITY, self.config.intensity)
        self.set(SensorSettings.MANUFACTURER, self.sensor.manufacturer)

        # Start the reading thread
        self.start_reading()

    def set(self, attr: SensorSettings, value: Any) -> Any:
        """
        Configures sensor settings like resolution, frame rate (FPS), intensity, etc.

        :param attr: The sensor setting to configure.
        :type attr: SensorSettings
        :param value: The value to set for the specified attribute.
        :type value: Any
        :raises TypeError: If an unsupported attribute is passed.
        """
        if not isinstance(attr, SensorSettings):
            raise TypeError(f"Expected attr to be of type SensorSettings but found {type(attr)} instead")

        if attr == SensorSettings.RESOLUTION:
            self.config.set_resolution(resolution=value)
            self.sensor.set_fps(self.config.fps)
            self.sensor.set_resolution(Digit.STREAMS[self.config.resolution])

        elif attr == SensorSettings.FPS:
            self.config.set_fps(fps=value)
            self.sensor.set_fps(self.config.fps)
            self.sensor.set_resolution(Digit.STREAMS[self.config.resolution])

        elif attr == SensorSettings.INTENSITY:
            self.config.intensity = value
            self.sensor.set_intensity(value)

        elif attr == SensorSettings.MANUFACTURER:
            self.config.manufacturer = value

        elif attr == SensorSettings.INTENSITY_RGB:
            if isinstance(value, list) and len(value) == 3:
                self.config.intensity = self.sensor.set_intensity_rgb(*value)
            else:
                raise TypeError(
                    f"Expected value to be a list with length of 3 but found {type(value)} with length "
                    f"{len(value) if isinstance(value, list) else 'N/A'} instead")

        else:
            warnings.warn("The Digit sensor only supports the following options to be set: RESOLUTION, FPS, "
                          "INTENSITY, MANUFACTURER and INTENSITY_RGB. The provided attribute did not match any of "
                          "these options and was skipped.", stacklevel=2)

    def get(self, attr: SensorSettings) -> Any:
        """
        Retrieves the current value of the specified sensor setting.

        :param attr: The sensor setting to retrieve.
        :type attr: SensorSettings
        :returns: The current value of the specified setting.
        :rtype: Any
        :raises TypeError: If an unsupported attribute is passed.
        """
        if not isinstance(attr, SensorSettings):
            raise TypeError(f"Expected attr to be of type SensorSettings but found {type(attr)} instead")
        return getattr(self.config, attr.name.lower(), None)

    def read(self, attr: DataStream, value: Any = None) -> Optional[Image]:
        """
        Reads data from the sensor, such as a frame. Returns the requested data or None if not available.

        :param attr: The data stream to read (e.g., a frame).
        :type attr: DataStream
        :param value: Optional argument, not used currently.
        :type value: Any
        :returns: The requested data (e.g., an Image object), or None if unavailable.
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

    def show(self, attr: DataStream):
        """
        Displays the live feed from the sensor, showing the frames as they are read.

        :param attr: The data stream to display (e.g., a frame).
        :type attr: DataStream
        :raises TypeError: If an unsupported data stream is passed.
        """
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
        """
        Calibrates the sensor by averaging a series of captured frames.

        :param num_frames: The number of frames to capture for calibration.
        :type num_frames: int
        :param skip_frames: The number of initial frames to skip before capturing.
        :type skip_frames: int
        :returns: The averaged frame used for calibration.
        :rtype: Optional[Image]
        """
        interval: float = 1.0 / self.config.fps

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
        """
        Disconnects the sensor, stopping any ongoing threads and releasing resources.
        """
        self.stop_event.set()
        self.recording_event.set()
        if self.reading_thread:
            self.reading_thread.join()
        if self.recording_thread:
            self.recording_thread.join()
        self.sensor.disconnect()

    def start_reading(self):
        """
        Starts a background thread that reads data from the sensor at the configured sampling frequency.
        """

        def read_sensor():
            interval = 1.0 / self.config.sampling_frequency
            while not self.stop_event.is_set():
                start_time = time.time()
                try:
                    frame = self.sensor.get_frame()
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
        """
        Starts a background thread that records data from the sensor into an HDF5 file
        at the configured recording frequency.
        """
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
        """Stops the ongoing recording session."""
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_event.set()
            self.recording_thread.join()
            self.recording_thread = None

        self.recording = False

    def _to_filtered_dict(self) -> Dict:
        """
        Returns a dictionary of filtered sensor configuration attributes.

        :returns: A dictionary containing relevant sensor configuration attributes.
        :rtype: Dict
        """
        include_keys: List[str] = [
            'sensor_name', 'sensor_type', 'serial_id', 'manufacturer',
            'fps', 'intensity', 'resolution', 'sampling_frequency',
            'recording_frequency'
        ]
        data: Dict = self.config.dict()
        filtered_data: Dict = {key: value for key, value in data.items() if key in include_keys}
        return filtered_data
