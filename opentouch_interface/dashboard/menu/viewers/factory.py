from typing import List

from opentouch_interface.interface.touch_sensor import TouchSensor
from opentouch_interface.dashboard.menu.viewers.image.file_viewer import FileViewer


class ViewerFactory:
    """
    Factory class to create instances of viewer classes based on sensor type.
    """
    def __new__(cls, sensor: TouchSensor, sensor_type: 'TouchSensor.SensorType', *args, **kwargs):
        if sensor_type == TouchSensor.SensorType.DIGIT:
            try:
                from opentouch_interface.dashboard.menu.viewers.image.digit_viewer import DigitViewer
                return DigitViewer(sensor)
            except ImportError as e:
                raise ImportError("DigitViewer dependencies are not installed. Please install them using 'pip install"
                                  "digit-interface'") from e

        elif sensor_type == TouchSensor.SensorType.FILE:
            return FileViewer(sensor)

        else:
            raise ValueError(f'Invalid sensor type {sensor_type}')
