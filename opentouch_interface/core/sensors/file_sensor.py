import threading
import time
from typing import Any, Optional
import cv2
import warnings

from opentouch_interface.core.dataclasses.buffer import CentralBuffer
from opentouch_interface.core.dataclasses.image.image_player import ImagePlayer
from opentouch_interface.core.validation.file_config import FileConfig
from opentouch_interface.core.dataclasses.options import SensorSettings, DataStream
from opentouch_interface.core.sensors.touch_sensor import TouchSensor
from opentouch_interface.core.dataclasses.image.image import Image


class FileSensor(TouchSensor):
    """
    A sensor class that simulates reading data from a sequence of frames (e.g., a video or a file of images).

    This class manages the reading of frames and supports operations like setting frame indices,
    showing frames, and fetching frames through a central buffer in a thread-safe way.

    :param config: Configuration object containing settings for the file-based sensor.
    :type config: FileConfig
    """

    def __init__(self, config: FileConfig):
        super().__init__(config=config)
        self.central_buffer: CentralBuffer = CentralBuffer()

        self.reading_thread: Optional[threading.Thread] = None
        self.stop_event: threading.Event = threading.Event()

    def initialize(self) -> None:
        """Initializes the sensor by creating an ImagePlayer to manage the sequence of frames."""
        self.sensor = ImagePlayer(frames=self.config.frames, fps=self.config.recording_frequency)

    def connect(self) -> None:
        """Starts the reading thread to begin reading frames from the file."""
        self.start_reading()

    def set(self, attr: SensorSettings, value: Any) -> Any:
        """
        Sets a configuration attribute for the sensor. Only the 'current_frame_index' can be set.

        :param attr: The sensor setting to set (must be `CURRENT_FRAME_INDEX`).
        :type attr: SensorSettings
        :param value: The value to set for the specified attribute.
        :type value: Any
        :raises TypeError: If an unsupported attribute is passed.
        """
        if attr == SensorSettings.CURRENT_FRAME_INDEX:
            self.config.current_frame_index = value
        else:
            raise TypeError(f"Only 'current_frame_index' can be set, but '{attr}' was provided.")

    def get(self, attr: SensorSettings) -> Any:
        """
        Retrieves the current value of a sensor setting from the configuration.

        :param attr: The sensor setting to retrieve.
        :type attr: SensorSettings
        :returns: The current value of the specified setting.
        :rtype: Any
        :raises TypeError: If an unsupported attribute is passed.
        """
        if not isinstance(attr, SensorSettings):
            raise TypeError(f"Expected attr to be of type SensorSettings but found {type(attr)} instead.")
        return getattr(self.config, attr.name.lower(), None)

    def read(self, attr: DataStream, value: Any = None) -> Optional[Image]:
        """
        Reads the next frame from the central buffer. If no frame is available, returns None.

        :param attr: The data stream to read (must be `FRAME`).
        :type attr: DataStream
        :param value: Unused parameter, reserved for future use.
        :type value: Any
        :returns: The next image from the buffer, or None if no image is available.
        :rtype: Optional[Image]
        :raises TypeError: If an unsupported data stream is passed.
        """
        if not isinstance(attr, DataStream):
            raise TypeError(f"Expected attr to be of type DataStream but found {type(attr)} instead.")
        if attr == DataStream.FRAME:
            return self.central_buffer.get()
        else:
            warnings.warn(f"The provided attribute '{attr}' did not match any available attribute. Returning None.")
            return None

    def show(self, attr: DataStream, recording: bool = False) -> None:
        """
        Displays the frames read from the central buffer in a window.

        :param attr: The data stream to display (must be `FRAME`).
        :type attr: DataStream
        :param recording: Flag to indicate whether to display recording frames (not used in this implementation).
        :type recording: bool
        :raises TypeError: If an unsupported data stream is passed.
        """
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
        """
        Calibration is not applicable for FileSensor as it reads from static files.

        :param num_frames: The number of frames to capture for calibration (not used).
        :type num_frames: int
        :param skip_frames: The number of initial frames to skip before capturing (not used).
        :type skip_frames: int
        """
        pass

    def disconnect(self) -> None:
        """Stops the reading thread and disconnects the sensor."""
        self.stop_event.set()
        if self.reading_thread:
            self.reading_thread.join()

    def start_reading(self) -> None:
        """
        Starts reading data from the file in a separate thread, pushing frames to the central buffer
        at the configured frame rate.
        """

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
        """No-op: Recording is not applicable for the FileSensor."""
        pass

    def stop_recording(self) -> None:
        """No-op: Recording is not applicable for the FileSensor."""
        pass
