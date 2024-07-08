from opentouch_interface.dashboard.menu.viewers.image.digit_viewer import DigitViewer
from opentouch_interface.dashboard.menu.viewers.image.file_viewer import FileViewer
from opentouch_interface.interface.touch_sensor import TouchSensor


class ViewerFactory:
    """
    Factory class to create instances of viewer classes based on sensor type.
    """
    def __new__(cls, sensor: TouchSensor, sensor_type: 'TouchSensor.SensorType', *args, **kwargs):
        if sensor_type == TouchSensor.SensorType.DIGIT:
            return DigitViewer(sensor)
        # elif sensor_type == TouchSensor.SensorType.GELSIGHT_MINI:
        #     return GelsightMiniViewer(sensor)
        elif sensor_type == TouchSensor.SensorType.FILE:
            return FileViewer(sensor)
        else:
            raise ValueError(f'Invalid sensor type {sensor_type}')
