import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

import cv2

from opentouch_interface.dataclasses.image import ImageWriter
from opentouch_interface.options import Streams, SetOptions


class TouchSensor(ABC):
    """
    This interface defines the expected behavior for any touch sensor object.

    Concrete sensor implementations can extend this interface to provide
    specific functionalities for different touch sensor.
    """

    class SensorType(Enum):
        DIGIT = "Digit"
        GELSIGHT_MINI = "Gelsight Mini"
        FILE = "File"

    def __init__(self, sensor_type: SensorType):
        self.sensor_type = sensor_type
        self.settings = {}

    @abstractmethod
    def initialize(self, name: str, serial: str, path: str) -> None:
        """
        Initializes the sensor.

        Args:
            name (str): The name or identifier for the sensor.
            serial (str): An optional initial value for the sensor (e.g., its serial number)
            path (str): Where should data be stored to or loaded from?
        """
        pass

    @abstractmethod
    def connect(self):
        """
        Establishes a connection with the sensor.
        """
        pass

    @abstractmethod
    def set(self, attr: Enum, value: Any) -> Any:
        """
        Sets a specific attribute of the sensor.

        Args:
            attr (str): The name of the attribute to set (e.g., "resolution").
            value (Any): The new value for the attribute.
        """
        pass

    @abstractmethod
    def get(self, attr: Enum) -> Any:
        pass

    @abstractmethod
    def read(self, attr: Enum, value: Any = None) -> Any:
        """
        If a sensor supports different data streams, choose one of them.

        Args:
            attr (str): The name of the data stream to read (e.g., "frame").
            value (Any, optional): Specify reading settings.

        Returns:
            Any: The current value of the attribute read from the sensor.
        """
        pass

    @abstractmethod
    def show(self, attr: Enum, recording: bool = False) -> Any:
        """
        Provides a way to display the value of a specific data stream
        (implementation might vary depending on the sensor type).

        Args:
            attr (str): The name of the data stream to display (e.g., "frame").
            recording (Any, optional): Specify showing settings.
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        Closes the connection with the sensor hardware.
        """
        pass
