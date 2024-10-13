from opentouch_interface.dashboard.viewers.image.sensor_viewer import SensorViewer
from opentouch_interface.core.sensors.file_sensor import FileSensor
from opentouch_interface.core.sensors.touch_sensor import TouchSensor
from opentouch_interface.dashboard.viewers.image.file_viewer import FileViewer
from opentouch_interface.dashboard.viewers.image.gelsight_viewer import GelsightViewer
from opentouch_interface.core.sensors.gelsight_mini import GelsightMiniSensor


class ViewerFactory:
    """
    Factory class to create viewer instances based on the type of sensor.

    The factory dynamically creates the appropriate viewer class (e.g., `DigitViewer`, `GelsightViewer`,
    or `FileViewer`) based on the provided `sensor` and its `sensor_type`.
    If necessary dependencies for a particular viewer are not installed, an ImportError is raised.
    """

    def __new__(cls, sensor: TouchSensor, sensor_type: 'TouchSensor.SensorType', *args, **kwargs) -> SensorViewer:
        """
        Creates a new viewer instance based on the provided sensor type.

        :param sensor: The sensor for which the viewer is being created. It should be an instance of a subclass of
                       `TouchSensor`.
        :param sensor_type: The type of the sensor, used to determine the appropriate viewer to instantiate.
        :param args: Additional positional arguments passed to the viewer's constructor.
        :param kwargs: Additional keyword arguments passed to the viewer's constructor.

        :return: An instance of a subclass of `SensorViewer` (e.g., `DigitViewer`, `GelsightViewer`, `FileViewer`).
        :rtype: SensorViewer
        :raises ImportError: If dependencies for a specific viewer are not installed (e.g., `digit-interface`).
        :raises ValueError: If the provided `sensor_type` is not recognized.
        """

        # Handle Digit sensor
        if sensor_type == TouchSensor.SensorType.DIGIT:
            try:
                from opentouch_interface.dashboard.viewers.image.digit_viewer import DigitViewer
                from opentouch_interface.core.sensors.digit import DigitSensor
                if isinstance(sensor, DigitSensor):
                    return DigitViewer(sensor)
            except ImportError as e:
                raise ImportError(
                    "DigitViewer dependencies are not installed. "
                    "Please install them using 'pip install digit-interface'."
                ) from e

        # Handle Gelsight Mini sensor
        if sensor_type == TouchSensor.SensorType.GELSIGHT_MINI:
            if isinstance(sensor, GelsightMiniSensor):
                return GelsightViewer(sensor)

        # Handle File sensor
        if sensor_type == TouchSensor.SensorType.FILE:
            if isinstance(sensor, FileSensor):
                return FileViewer(sensor)

        # If sensor type is unrecognized
        raise ValueError(f'Invalid sensor type: {sensor_type}')
