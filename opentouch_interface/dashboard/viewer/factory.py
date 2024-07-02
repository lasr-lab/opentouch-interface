from opentouch_interface.dashboard.viewer.sensors.digit_viewer import DigitViewer
from opentouch_interface.dashboard.viewer.sensors.gelsight_mini_viewer import GelsightMiniViewer
from opentouch_interface.touch_sensor import TouchSensor


class ViewerFactory:
    """
    Factory class to create instances of viewer classes based on sensor type.
    """
    def __new__(cls, sensor: TouchSensor, sensor_type: 'TouchSensor.SensorType', *args, **kwargs):
        if sensor_type == TouchSensor.SensorType.DIGIT:
            return DigitViewer(sensor)
        elif sensor_type == TouchSensor.SensorType.GELSIGHT_MINI:
            return GelsightMiniViewer(sensor)
        else:
            raise ValueError(f'Invalid sensor type {sensor_type}')
