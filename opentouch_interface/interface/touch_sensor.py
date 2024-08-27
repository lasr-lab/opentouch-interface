import pprint
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from opentouch_interface.interface.dataclasses.image.image import Image
from opentouch_interface.interface.dataclasses.validation.sensors.sensor_config import SensorConfig
from opentouch_interface.interface.options import SensorSettings, DataStream


class TouchSensor(ABC):
    """
    This interface defines the expected behavior for any touch sensor object.

    Concrete sensor implementations can extend this interface to provide
    specific functionalities for different touch sensors.
    """

    class SensorType(Enum):
        DIGIT = "Digit"
        GELSIGHT_MINI = "Gelsight Mini"
        FILE = "File"

    def __init__(self, config: SensorConfig):
        """
        Initializes the touch sensor with a specific type.

        :param config: Config for that sensor
        """
        self.config: SensorConfig = config
        self.sensor = None

        self.path: str = ""
        self.recording: bool = False

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the touch sensor with necessary parameters.

        :return: None.
        """
        pass

    @abstractmethod
    def connect(self) -> None:
        """
        Establish a connection to the touch sensor.

        This method should be implemented to handle any necessary
        operations to connect the sensor to its data source.
        """
        pass

    @abstractmethod
    def calibrate(self, num_frames: int = 100, skip_frames: int = 20) -> Any:
        """
        Calibrate the touch sensor.

        :param num_frames: Number of frames to use for calibration.
        :param skip_frames: Number of initial frames to skip (not included in num_frames).
        :return: The average image calculated by num_frames.
        """
        pass

    @abstractmethod
    def set(self, attr: SensorSettings, value: Any) -> Any:
        """
        Set a specific attribute of the touch sensor.

        :param attr: The attribute to set (defined in SetOptions).
        :param value: The value to set the attribute to.
        :return: Result or status of the set operation. If the attribute is not available, None is returned.
        """
        pass

    @abstractmethod
    def get(self, attr: SensorSettings) -> Any:
        """
        Get a specific attribute of the touch sensor.

        :param attr: The attribute to get (defined in SetOptions).
        :return: The current value of the attribute. If the attribute is not available, None is returned.
        """
        pass

    @abstractmethod
    def read(self, attr: DataStream, value: Any = None) -> Any:
        """
        Read data from the touch sensor.

        :param attr: The data stream to read from (defined in Streams).
        :param value: Optional parameter for read configuration.
        :return: Data read from the sensor.
        """
        pass

    @abstractmethod
    def show(self, attr: DataStream) -> None:
        """
        Show the data stream from the touch sensor.

        :param attr: The data stream to show (defined in Streams).
        :return: None.
        """
        pass

    def info(self, verbose: bool = True):
        def format_value(value):
            if isinstance(value, list) and all(isinstance(item, Image) for item in value):
                # Truncate or summarize the list of Image objects
                return f"{len(value)} images"
            return value

        if verbose:
            formatted_dict = {k: format_value(v) for k, v in self.config.dict().items()}
            pprint.pprint(formatted_dict)

        # Return the potentially formatted dictionary
        return {k: format_value(v) for k, v in self.config.dict().items()}

    @abstractmethod
    def disconnect(self) -> None:
        """
        Disconnect the touch sensor.

        This method should be implemented to handle any necessary
        operations to properly disconnect the sensor from its data source.
        """
        pass

    @abstractmethod
    def start_recording(self) -> None:
        """
        Start the recording of the touch sensor.
        """
        pass

    @abstractmethod
    def stop_recording(self) -> None:
        """
        Stop the recording of the touch sensor.
        """
        pass
