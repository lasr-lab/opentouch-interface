from opentouch_interface.dashboard.menu.viewers.image.sensor_viewer import SensorViewer
from opentouch_interface.interface.sensors.digit import DigitSensor
from opentouch_interface.interface.sensors.file_sensor import FileSensor
from opentouch_interface.interface.sensors.gelsight_mini import GelsightMiniSensor
from opentouch_interface.interface.touch_sensor import TouchSensor
from opentouch_interface.dashboard.menu.viewers.image.file_viewer import FileViewer


class ViewerFactory:
    """
    Factory class to create instances of viewer classes based on sensor type.
    """
    def __new__(cls, sensor: TouchSensor, *args, **kwargs) -> SensorViewer:
        if isinstance(sensor, DigitSensor):
            try:
                from opentouch_interface.dashboard.menu.viewers.image.digit_viewer import DigitViewer
                return DigitViewer(sensor)
            except ImportError as e:
                raise ImportError("DigitViewer dependencies are not installed. Please install them using 'pip install"
                                  " digit-interface'") from e

        if isinstance(sensor, GelsightMiniSensor):
            try:
                from opentouch_interface.dashboard.menu.viewers.image.gelsight_viewer import GelsightViewer
                return GelsightViewer(sensor)
            except ImportError as e:
                raise ImportError("Gelsight Mini dependencies are not installed. Please install them using 'pip install"
                                  " gelsight@git+https://github.com/gelsightinc/gsrobotics") from e

        if isinstance(sensor, FileSensor):
            return FileViewer(sensor)

        else:
            raise ValueError(f'Invalid sensor type {type(sensor)}')
