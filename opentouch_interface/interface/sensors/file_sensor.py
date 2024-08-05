import base64
import threading
import time
from typing import Any, Union, Dict, List
from io import BytesIO
import cv2
import warnings
from pydantic import BaseModel, Field, ValidationError, model_validator

from opentouch_interface.interface.dataclasses.buffer import CentralBuffer
from opentouch_interface.interface.options import SensorSettings, DataStream
from opentouch_interface.interface.touch_sensor import TouchSensor
from opentouch_interface.interface.dataclasses.image import Image, ImageReader


class FileConfig(BaseModel, validate_assignment=True, arbitrary_types_allowed=True):
    """A configuration model for the File sensor."""

    sensor_name: str
    """The name of the sensor"""
    sensor_type: str = Field(default="FILE", literal=True, description="Sensor type (must be 'FILE')")
    """The type of the sensor, defaults to 'FILE'"""
    path: Union[str, None] = None
    """The file path for reading data, defaults to None"""
    file: Union[str, BytesIO, None] = None
    """The file-like object for reading data, defaults to None"""
    frames: List[Any] = Field(default_factory=list)
    """List to store frames, defaults to an empty list"""
    current_frame_index: int = Field(default=0)
    """Index of the current frame, defaults to 0"""
    recording: bool = Field(default=False, literal=True, description="Whether the sensor is recording (must be false)")
    """Whether the sensor is recording (must be false, as FileSensor can only replay data)"""
    stream: Union[str, DataStream] = Field(DataStream.FRAME, description="Stream type (FRAME)")
    '''The stream type, must be "FRAME", defaults to "FRAME"'''

    @model_validator(mode='after')
    def validate_model(self):
        # Validate stream
        if not isinstance(self.stream, DataStream):
            if not isinstance(self.stream, str) or self.stream != "FRAME":
                raise ValueError(f"Invalid stream '{self.stream}': Stream must be a str set to 'FRAME'")
            self.stream: DataStream = DataStream.FRAME

        # Validate path and file
        path, file = self.path, self.file
        if path is not None and file is not None:
            raise ValueError('Either path or file must be provided, but not both.')
        if path is None and file is None:
            raise ValueError('Either path or file must be provided.')
        if path and not path.endswith('.h5'):
            raise ValueError(f"Invalid path '{path}': Path must be a .h5 file.")

        # Convert file from base64 to BytesIO
        if file and isinstance(file, str):
            self.file = BytesIO(base64.b64decode(file))


class FileSensor(TouchSensor):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config=self._validate_and_update_config(config))
        self.central_buffers = {}
        self.reading_threads = {}
        self.stop_events = {}

    @staticmethod
    def _validate_and_update_config(config: Dict[str, Any]) -> FileConfig:
        try:
            return FileConfig(**config)
        except ValidationError as e:
            raise ValueError(f"Invalid configuration: {e}")

    def initialize(self) -> None:
        self.sensor = ImageReader(file=self.config.file, path=self.config.path)
        for sensor_name in self.sensor.get_sensor_names():
            self.central_buffers[sensor_name] = CentralBuffer()
            self.stop_events[sensor_name] = threading.Event()

    def connect(self):
        # Start a reading thread for each sensor
        for sensor_name in self.sensor.get_sensor_names():
            self.start_reading(sensor_name)

    def set(self, attr: SensorSettings, value: Any) -> Any:
        if attr == SensorSettings.CURRENT_FRAME_INDEX:
            # Set the current frame index for each sensor
            for sensor_name in self.sensor.get_sensor_names():
                self.config.current_frame_index[sensor_name] = value
        else:
            raise TypeError(f"Only 'current_frame_index' can be set, but '{attr}' was provided.")

    def get(self, attr: SensorSettings) -> Any:
        if not isinstance(attr, SensorSettings):
            raise TypeError(f"Expected attr to be of type SensorSettings but found {type(attr)} instead.")
        return getattr(self.config, attr.name.lower(), None)

    def read(self, attr: DataStream, value: Any = None, sensor_name: str = None) -> Image | None:
        if not isinstance(attr, DataStream):
            raise TypeError(f"Expected attr to be of type DataStream but found {type(attr)} instead.")
        if sensor_name is None:
            raise ValueError(f"Sensor name must be provided but got {sensor_name}.")
        if attr == DataStream.FRAME and sensor_name:
            return self.central_buffers[sensor_name].get()
        else:
            warnings.warn(f"The provided attribute '{attr}' or sensor '{sensor_name}' did not match any available "
                          f"attribute or sensor. Returning None.")
            return None

    # TODO: This doesn't work yet
    def show(self, attr: DataStream, recording: bool = False, sensor_name: str = None):
        if not isinstance(attr, DataStream):
            raise TypeError(f"Expected attr to be of type DataStream but found {type(attr)} instead.")

        def display_frame(s_name: str):
            cv2.namedWindow(f'File view - {s_name}', cv2.WINDOW_NORMAL)
            cv2.resizeWindow(f'File view - {s_name}', 640, 480)  # Adjust size as needed
            while True:
                frame = self.read(DataStream.FRAME, sensor_name=s_name)
                if frame is not None:
                    cv2.imshow(f'File view - {s_name}', frame.as_cv2())
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                else:
                    break
            cv2.destroyWindow(f'File view - {s_name}')

        if attr == DataStream.FRAME:
            if sensor_name:
                display_frame(sensor_name)
            else:
                threads = []
                for s_name in self.sensor.get_sensor_names():
                    t = threading.Thread(target=display_frame, args=(s_name,))
                    t.start()
                    threads.append(t)

                for t in threads:
                    t.join()
        else:
            warnings.warn(
                f"The provided attribute '{attr}' or sensor '{sensor_name}' did not match any available "
                f"attribute or sensor.",
                stacklevel=2)

    def calibrate(self, num_frames: int = 100, skip_frames: int = 20) -> None:
        # Calibration is not applicable for FileSensor as it reads static files.
        pass

    def disconnect(self):
        for sensor_name in self.sensor.get_sensor_names():
            self.stop_events[sensor_name].set()
            if self.reading_threads[sensor_name]:
                self.reading_threads[sensor_name].join()

    def start_reading(self, sensor_name: str):
        """Start reading data from the file in a separate thread for the given sensor at the fps specified by the
        ImageReader."""
        def read_file(s_name: str):
            interval = 1.0 / self.sensor.fps
            while not self.stop_events[s_name].is_set():
                start_time = time.time()
                frame = self.sensor.get_next_frame(s_name)
                if frame:
                    self.central_buffers[s_name].put(frame)
                elapsed_time = time.time() - start_time
                time_to_sleep = interval - elapsed_time
                if time_to_sleep > 0:
                    time.sleep(time_to_sleep)

        self.reading_threads[sensor_name] = threading.Thread(target=read_file, args=(sensor_name,))
        self.reading_threads[sensor_name].start()

    def start_recording(self) -> None:
        pass

    def stop_recording(self) -> None:
        pass
