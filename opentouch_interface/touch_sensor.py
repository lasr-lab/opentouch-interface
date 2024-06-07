from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class TouchSensor(ABC):
    """
    This interface defines the expected behavior for any touch sensor object.

    Concrete sensor implementations can extend this interface to provide
    specific functionalities for different touch sensor.
    """

    @abstractmethod
    def initialize(self, name: str, value: Any) -> None:
        """
        Initializes the sensor.

        Args:
            name (str): The name or identifier for the sensor.
            value (Any): An optional initial value for the sensor (e.g., its serial number)
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
    def show(self, attr: Enum, value: Any = None) -> Any:
        """
        Provides a way to display the value of a specific data stream
        (implementation might vary depending on the sensor type).

        Args:
            attr (str): The name of the data stream to display (e.g., "frame").
            value (Any, optional): Specify showing settings.
        """
        pass

    @abstractmethod
    def close(self):
        """
        Closes the connection with the sensor hardware.
        """
        pass
