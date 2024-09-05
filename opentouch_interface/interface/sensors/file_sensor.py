import threading
import time
from typing import Any, Optional
import cv2
import warnings

from opentouch_interface.interface.dataclasses.buffer import CentralBuffer
from opentouch_interface.interface.dataclasses.image.image_player import ImagePlayer
from opentouch_interface.interface.dataclasses.validation.sensors.file_config import FileConfig
from opentouch_interface.interface.options import SensorSettings, DataStream
from opentouch_interface.interface.touch_sensor import TouchSensor
from opentouch_interface.interface.dataclasses.image.image import Image


class FileSensor(TouchSensor):
    def __init__(self, config: FileConfig):
        super().__init__(config=config)
        self.central_buffer: CentralBuffer = CentralBuffer()

        self.reading_thread: Optional[threading.Thread] = None
        self.stop_event: threading.Event = threading.Event()

    def initialize(self) -> None:
        self.sensor = ImagePlayer(frames=self.config.frames, fps=self.config.recording_frequency)

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
                frame = self.sensor.next_frame()
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
