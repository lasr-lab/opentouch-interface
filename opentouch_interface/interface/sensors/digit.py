import threading
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import os
import warnings

import cv2
import numpy as np
from pydantic import BaseModel, Field, ValidationError, PrivateAttr, model_validator

from opentouch_interface.interface.dataclasses.buffer import CentralBuffer
from opentouch_interface.interface.options import SensorSettings, DataStream
from opentouch_interface.interface.touch_sensor import TouchSensor
from opentouch_interface.interface.dataclasses.image import Image, ImageWriter
from digit_interface.digit import Digit


class DigitConfig(BaseModel, validate_assignment=True, arbitrary_types_allowed=True):
    """A configuration model for the DIGIT sensor."""

    sensor_name: str
    """The name of the sensor"""
    sensor_type: str = Field(default="DIGIT", literal=True, description="Sensor type (must be 'DIGIT')")
    '''The type of the sensor, defaults to "DIGIT"'''
    serial_id: str
    """The serial ID of the sensor"""
    manufacturer: str = Field(default="")
    """The manufacturer of the sensor, defaults to an empty string"""
    path: Optional[str] = None
    """The file path for saving data, defaults to None."""
    fps: int = Field(30, description="Frame rate (must be 30 or 60)")
    """The frame rate, must be either 30 or 60, defaults to 30."""
    intensity: int = Field(15, ge=0, le=15, description="Intensity level (0-15)")
    """The intensity level, ranges from 0 to 15, defaults to 15."""
    resolution: str = Field('QVGA', pattern='^(VGA|QVGA)$', description="Resolution (VGA or QVGA)")
    """The resolution, either "VGA" or "QVGA", defaults to "QVGA"."""
    stream: Union[str, DataStream] = Field(DataStream.FRAME, description="Stream type (FRAME)")
    '''The stream type, must be "FRAME", defaults to "FRAME"'''
    recording: bool = False
    '''Flag to indicate if recording is active, defaults to False'''
    _calibration: Image = PrivateAttr(default=None)
    '''Private attribute to store the calibration image, defaults to None'''
    sampling_frequency: int = Field(30, description="Sampling frequency in Hz")
    '''The sampling frequency in Hz, defaults to 30Hz'''
    recording_frequency: int = Field(sampling_frequency, description="Recording frequency in Hz")
    '''The recording frequency in Hz, defaults to sampling_frequency (which by default is 30Hz)'''

    @model_validator(mode='after')
    def validate_model(self):
        # Validate path
        if self.path is None:
            self.path = f"{self.sensor_type}-{self.sensor_name}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.h5"
        if not self.path.endswith('.h5'):
            raise ValueError('Path must have a .h5 extension')
        if os.path.exists(self.path):
            raise ValueError('File already exists')

        # Validate fps
        if self.fps not in [30, 60]:
            raise ValueError('FPS must be either 30 or 60')

        # Validate stream
        if not isinstance(self.stream, DataStream):
            if not isinstance(self.stream, str) or self.stream != "FRAME":
                raise ValueError('Stream must be a str set to "FRAME"')
            self.stream: DataStream = DataStream.FRAME


class DigitSensor(TouchSensor):

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config=self._validate_and_update_config(config))
        self.central_buffer = CentralBuffer()
        self.reading_thread = None
        self.recording_thread = None
        self.stop_event = threading.Event()
        self.recording_event = threading.Event()

    @staticmethod
    def _validate_and_update_config(config: Dict[str, Any]) -> DigitConfig:
        try:
            return DigitConfig(**config)
        except ValidationError as e:
            raise ValueError(f"Invalid configuration: {e}")

    def initialize(self) -> None:
        self.sensor = Digit(serial=self.config.serial_id, name=self.config.sensor_name)

    def connect(self):
        self.sensor.connect()
        self.set(SensorSettings.RESOLUTION, self.config.resolution)
        self.set(SensorSettings.FPS, self.config.fps)
        self.set(SensorSettings.INTENSITY, self.config.intensity)
        self.set(SensorSettings.MANUFACTURER, self.sensor.manufacturer)

        # Start the reading thread
        self.start_reading()

        if self.config.recording:
            self.start_recording()  # Start recording if configured to do so

    def set(self, attr: SensorSettings, value: Any) -> Any:
        if not isinstance(attr, SensorSettings):
            raise TypeError(f"Expected attr to be of type SensorSettings but found {type(attr)} instead.\n")

        if attr == SensorSettings.RESOLUTION:
            self.config.resolution = value
            self.sensor.set_resolution(Digit.STREAMS[value])

        elif attr == SensorSettings.FPS:
            self.config.fps = value
            self.sensor.set_fps(value)

        elif attr == SensorSettings.INTENSITY:
            self.config.intensity = value
            self.sensor.set_intensity(value)

        elif attr == SensorSettings.MANUFACTURER:
            self.config.manufacturer = value

        elif attr == SensorSettings.INTENSITY_RGB:
            if isinstance(value, List) and len(value) == 3:
                self.config.intensity = self.sensor.set_intensity_rgb(*value)
            else:
                raise TypeError(f"Expected value must be of type list with length of 3 but found "
                                f"{type(value)} with length {len(value) if isinstance(value, List) else 'N/A'} "
                                f"instead\n")

        else:
            warnings.warn("The Digit sensor only supports the following options to be set: RESOLUTION, FPS, "
                          "INTENSITY, MANUFACTURER and INTENSITY_RGB. The provided attribute did not match any of "
                          "these options and was skipped.\n", stacklevel=2)

    def get(self, attr: SensorSettings) -> Any:
        if not isinstance(attr, SensorSettings):
            raise TypeError(f"Expected attr to be of type SensorSettings but found {type(attr)} instead.\n")
        return getattr(self.config, attr.name.lower(), None)

    def read(self, attr: DataStream, value: Any = None) -> Image | None:
        if not isinstance(attr, DataStream):
            raise TypeError(f"Expected attr to be of type DataStream but found {type(attr)} instead.\n")

        if attr == DataStream.FRAME:
            return self.central_buffer.get()
        else:
            warnings.warn("The provided attribute did not match any available attribute.\n")
            return None

    def show(self, attr: DataStream) -> Any:
        if not isinstance(attr, DataStream):
            raise TypeError(f"Expected attr to be of type DataStream but found {type(attr)} instead.\n")

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
            warnings.warn("The provided attribute did not match any available attribute.\n", stacklevel=2)
            return None

    def calibrate(self, num_frames: int = 100, skip_frames: int = 20) -> Image | None:
        interval = 1.0 / self.config.fps

        # Skip the initial frames
        skipped = 0
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
                frame = self.sensor.get_frame()
                if frame is not None:
                    self.central_buffer.put(Image(image=frame, rotation=(0, 1, 2)))
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

        def record_data():
            interval = 1.0 / self.config.recording_frequency
            with ImageWriter(file_path=self.config.path, fps=self.config.recording_frequency) as recorder:
                while not self.stop_event.is_set():
                    start_time = time.time()
                    image = self.read(attr=DataStream.FRAME)
                    if image:
                        recorder.save(image)
                    elapsed_time = time.time() - start_time
                    time_to_sleep = interval - elapsed_time
                    if time_to_sleep > 0:
                        time.sleep(time_to_sleep)

        self.recording_thread = threading.Thread(target=record_data)
        self.recording_thread.start()

    def stop_recording(self):
        """Stop the ongoing recording."""
        if self.recording_thread and self.recording_thread.is_alive():
            self.stop_event.set()
            self.recording_thread.join()
            self.recording_thread = None
