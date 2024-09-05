from opentouch_interface.dashboard.menu.viewers.image.sensor_viewer import SensorViewer
from opentouch_interface.interface.sensors.file_sensor import FileSensor
from opentouch_interface.interface.touch_sensor import TouchSensor
from opentouch_interface.dashboard.menu.viewers.image.file_viewer import FileViewer
from opentouch_interface.dashboard.menu.viewers.image.gelsight_viewer import GelsightViewer
from opentouch_interface.interface.sensors.gelsight_mini import GelsightMiniSensor


class ViewerFactory:
    """
    Factory class to create instances of viewer classes based on sensor type.
    """
    def __new__(cls, sensor: TouchSensor, sensor_type: 'TouchSensor.SensorType', *args, **kwargs) -> SensorViewer:
        if sensor_type == TouchSensor.SensorType.DIGIT:
            try:
                from opentouch_interface.dashboard.menu.viewers.image.digit_viewer import DigitViewer
                from opentouch_interface.interface.sensors.digit import DigitSensor
                if isinstance(sensor, DigitSensor):
                    return DigitViewer(sensor)
            except ImportError as e:
                raise ImportError("DigitViewer dependencies are not installed. Please install them using 'pip install"
                                  " digit-interface'") from e

        if sensor_type == TouchSensor.SensorType.GELSIGHT_MINI:
            if isinstance(sensor, GelsightMiniSensor):
                return GelsightViewer(sensor)

        if sensor_type == TouchSensor.SensorType.FILE:
            if isinstance(sensor, FileSensor):
                return FileViewer(sensor)

        else:
            raise ValueError(f'Invalid sensor type {type(sensor)}')
