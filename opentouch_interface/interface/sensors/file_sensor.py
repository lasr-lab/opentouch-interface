import base64
import threading
import time
from typing import Any, Union, Dict, List, Optional
from io import BytesIO
import cv2
import warnings
from pydantic import BaseModel, Field, ValidationError, model_validator

from opentouch_interface.interface.dataclasses.buffer import CentralBuffer
from opentouch_interface.interface.dataclasses.image.image_reader import ImageReader
from opentouch_interface.interface.options import SensorSettings, DataStream
from opentouch_interface.interface.touch_sensor import TouchSensor
from opentouch_interface.interface.dataclasses.image.image import Image


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
        self.central_buffer: CentralBuffer = CentralBuffer()
        self.reading_thread = None
        self.stop_event = threading.Event()

    @staticmethod
    def _validate_and_update_config(config: Dict[str, Any]) -> FileConfig:
        try:
            return FileConfig(**config)
        except ValidationError as e:
            raise ValueError(f"Invalid configuration: {e}")

    def initialize(self) -> None:
        self.sensor = ImageReader(file=self.config.file, path=self.config.path)
        self.config.frames = self.sensor.get_all_frames()

    def connect(self):
        # Start the reading thread
        self.start_reading()

    def set(self, attr: SensorSettings, value: Any) -> Any:
        if attr == SensorSettings.CURRENT_FRAME_INDEX:
            self.config.current_frame_index = value
        else:
            raise TypeError(f"Only 'current_frame_index' can be set, but '{attr}' was provided.")

    def get(self, attr: SensorSettings) -> Any:
        if not isinstance(attr, SensorSettings):
            raise TypeError(f"Expected attr to be of type SensorSettings but found {type(attr)} instead.")
        return getattr(self.config, attr.name.lower(), None)

    def read(self, attr: DataStream, value: Any = None) -> Optional[Image]:
        if not isinstance(attr, DataStream):
            raise TypeError(f"Expected attr to be of type DataStream but found {type(attr)} instead.")
        if attr == DataStream.FRAME:
            return self.central_buffer.get()
        else:
            warnings.warn(f"The provided attribute '{attr}' did not match any available attribute. Returning None.")
            return None

    def show(self, attr: DataStream, recording: bool = False):
        if not isinstance(attr, DataStream):
            raise TypeError(f"Expected attr to be of type DataStream but found {type(attr)} instead.")

        if attr == DataStream.FRAME:
            while True:
                frame = self.read(DataStream.FRAME)
                if frame is not None:
                    cv2.imshow('File view', frame.as_cv2())
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                else:
                    break
            cv2.destroyAllWindows()
        else:
            warnings.warn(f"The provided attribute '{attr}' did not match any available attribute.", stacklevel=2)

    def calibrate(self, num_frames: int = 100, skip_frames: int = 20) -> None:
        # Calibration is not applicable for FileSensor as it reads static files.
        pass

    def disconnect(self):
        self.stop_event.set()
        if self.reading_thread:
            self.reading_thread.join()

    def start_reading(self):
        """Start reading data from the file in a separate thread at the fps specified by the ImageReader."""
        def read_file():
            interval = 1.0 / self.sensor.fps
            while not self.stop_event.is_set():
                start_time = time.time()
                frame = self.sensor.get_next_frame()
                if frame:
                    self.central_buffer.put(frame)
                elapsed_time = time.time() - start_time
                time_to_sleep = interval - elapsed_time
                if time_to_sleep > 0:
                    time.sleep(time_to_sleep)

        self.reading_thread = threading.Thread(target=read_file)
        self.reading_thread.start()

    def start_recording(self) -> None:
        pass

    def stop_recording(self) -> None:
        pass
