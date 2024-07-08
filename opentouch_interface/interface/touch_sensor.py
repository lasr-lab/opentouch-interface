from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

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

    def __init__(self, sensor_type: SensorType):
        """
        Initializes the touch sensor with a specific type.

        :param sensor_type: The type of the touch sensor (e.g., DIGIT, GELSIGHT_MINI, FILE).
        """
        self.sensor_type = sensor_type
        self.settings = {}

    @abstractmethod
    def initialize(self, name: str, serial: str, path: str) -> None:
        """
        Initialize the touch sensor with necessary parameters.

        :param name: Name of the sensor.
        :param serial: Serial number of the sensor.
        :param path: Path where data is stored (and can be loaded from) when the sensor data is recorded.
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
    def calibrate(self, num_frames: int, skip_frames: int) -> Any:
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
    def show(self, attr: DataStream, recording: bool = False) -> None:
        """
        Show the data stream from the touch sensor.

        :param attr: The data stream to show (defined in Streams).
        :param recording: Whether to record the data while showing it.
        :return: None.
        """
        pass

    @abstractmethod
    def info(self, verbose: bool = True) -> dict:
        """
        Get information about the touch sensor.

        :param verbose: Whether to print detailed information.
        :return: A dictionary containing sensor information.
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Disconnect the touch sensor.

        This method should be implemented to handle any necessary
        operations to properly disconnect the sensor from its data source.
        """
        pass
