import pprint
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from opentouch_interface.core.dataclasses.image.image import Image
from opentouch_interface.core.validation.sensor_config import SensorConfig
from opentouch_interface.core.dataclasses.options import SensorSettings, DataStream


class TouchSensor(ABC):
    """
    This abstract base class defines the interface for any touch sensor object.

    Concrete sensor implementations (e.g., Digit, GelSight Mini) should extend this
    class and implement the required methods for sensor-specific functionalities.
    """

    class SensorType(Enum):
        """
        Enum representing different types of touch sensors.
        """
        DIGIT = "Digit"
        GELSIGHT_MINI = "Gelsight Mini"
        FILE = "File"

    def __init__(self, config: SensorConfig):
        """
        Initializes the touch sensor with a specific configuration.

        :param config: Configuration object containing sensor settings.
        :type config: SensorConfig
        """
        self.config: SensorConfig = config
        self.sensor = None

        self.path: str = ""  # Path for saving data or configuration files
        self.recording: bool = False  # Flag indicating whether the sensor is recording

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the touch sensor with the necessary parameters.
        This may include setting up connections, loading configurations, etc.

        :returns: None
        """
        pass

    @abstractmethod
    def connect(self) -> None:
        """
        Establish a connection to the touch sensor.

        This method should handle the necessary operations to connect
        the sensor to its data source (e.g., via USB or network).

        :returns: None
        """
        pass

    @abstractmethod
    def calibrate(self, num_frames: int = 100, skip_frames: int = 20) -> Any:
        """
        Calibrate the touch sensor using a number of frames.

        :param num_frames: The number of frames to use for calibration.
        :type num_frames: int
        :param skip_frames: The number of initial frames to skip (not included in num_frames).
        :type skip_frames: int
        :returns: The average image calculated from the frames.
        :rtype: Any
        """
        pass

    @abstractmethod
    def set(self, attr: SensorSettings, value: Any) -> Any:
        """
        Set a specific attribute of the touch sensor.

        :param attr: The sensor attribute to set (e.g., resolution, FPS).
        :type attr: SensorSettings
        :param value: The value to set for the specified attribute.
        :type value: Any
        :returns: Result or status of the set operation, or None if unsupported.
        :rtype: Any
        """
        pass

    @abstractmethod
    def get(self, attr: SensorSettings) -> Any:
        """
        Get a specific attribute of the touch sensor.

        :param attr: The sensor attribute to retrieve.
        :type attr: SensorSettings
        :returns: The current value of the specified attribute, or None if unavailable.
        :rtype: Any
        """
        pass

    @abstractmethod
    def read(self, attr: DataStream, value: Any = None) -> Any:
        """
        Read data from the touch sensor, such as a frame or intensity data.

        :param attr: The data stream to read from (e.g., frame).
        :type attr: DataStream
        :param value: Optional parameter for additional read configuration.
        :type value: Any
        :returns: Data read from the sensor, such as an image or data stream.
        :rtype: Any
        """
        pass

    @abstractmethod
    def show(self, attr: DataStream) -> None:
        """
        Display the data stream from the touch sensor (e.g., show live frames).

        :param attr: The data stream to display (e.g., frames).
        :type attr: DataStream
        :returns: None
        """
        pass

    def info(self, verbose: bool = True) -> dict:
        """
        Provides a summary of the sensor's configuration.

        :param verbose: If True, prints the formatted configuration information.
                        If False, returns the configuration as a dictionary.
        :type verbose: bool
        :returns: Dictionary of the sensor's configuration.
        :rtype: dict
        """

        def format_value(value):
            if isinstance(value, list) and all(isinstance(item, Image) for item in value):
                # Summarize the list of Image objects, e.g., 5 images
                return f"{len(value)} images"
            return value

        formatted_dict = {k: format_value(v) for k, v in self.config.dict().items()}

        if verbose:
            pprint.pprint(formatted_dict)

        return formatted_dict

    @abstractmethod
    def disconnect(self) -> None:
        """
        Disconnect the touch sensor and release any resources.

        This method should handle operations to safely disconnect the sensor
        from its data source and clean up any resources.

        :returns: None
        """
        pass

    @abstractmethod
    def start_recording(self) -> None:
        """
        Start recording data from the touch sensor.

        :returns: None
        """
        pass

    @abstractmethod
    def stop_recording(self) -> None:
        """
        Stop recording data from the touch sensor.

        :returns: None
        """
        pass
