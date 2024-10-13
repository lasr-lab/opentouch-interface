from opentouch_interface.core.validation.digit_config import DigitConfig
from opentouch_interface.core.validation.file_config import FileConfig
from opentouch_interface.core.validation.gelsight_config import GelsightConfig
from opentouch_interface.core.validation.sensor_config import SensorConfig
from opentouch_interface.core.sensors.file_sensor import FileSensor


class OpentouchInterface:
    """
    Factory class to create sensor instances based on the provided configuration.

    This class determines the appropriate sensor type (e.g., DigitSensor, GelsightMiniSensor, FileSensor)
    based on the configuration object passed to it and dynamically imports the corresponding sensor class.
    If dependencies for a specific sensor type are not installed, it raises an ImportError with installation instructions.
    """

    def __new__(cls, config: SensorConfig, *args, **kwargs):
        """
        Creates a new sensor instance based on the provided configuration.

        :param config: The configuration object that defines the type of sensor to instantiate. It can be an instance
                       of `DigitConfig`, `GelsightConfig`, or `FileConfig`.
        :type config: SensorConfig
        :param args: Additional positional arguments to pass to the sensor constructor.
        :param kwargs: Additional keyword arguments to pass to the sensor constructor.
        :return: An instance of the corresponding sensor (e.g., `DigitSensor`, `GelsightMiniSensor`, `FileSensor`).
        :raises ImportError: If the necessary dependencies for a specific sensor are not installed.
        :raises ValueError: If the provided configuration is not a recognized sensor config type.
        """

        # Handle Digit sensor configuration
        if isinstance(config, DigitConfig):
            try:
                from opentouch_interface.core.sensors.digit import DigitSensor
                return DigitSensor(config=config)
            except ImportError as e:
                raise ImportError(
                    "DigitSensor dependencies are not installed. "
                    "Please install them using 'pip install digit-interface'."
                ) from e

        # Handle Gelsight Mini sensor configuration
        if isinstance(config, GelsightConfig):
            try:
                from opentouch_interface.core.sensors.gelsight_mini import GelsightMiniSensor
                return GelsightMiniSensor(config=config)
            except ImportError as e:
                raise ImportError(
                    "Gelsight Mini dependencies are not installed. "
                    "Please install them using 'pip install gelsight@git+https://github.com/gelsightinc/gsrobotics'."
                ) from e

        # Handle File sensor configuration
        elif isinstance(config, FileConfig):
            return FileSensor(config=config)

        # Handle unknown sensor configuration
        else:
            raise ValueError(f"Invalid sensor config type: {type(config)}")
