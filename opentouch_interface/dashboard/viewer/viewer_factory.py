from opentouch_interface.dashboard.viewer.sensors.digit import DigitViewer
from opentouch_interface.dashboard.viewer.sensors.gelsight_mini import GelsightMiniViewer
from opentouch_interface.touch_sensor import TouchSensor


class ViewerFactory:
    def __new__(cls, sensor, sensor_type: 'TouchSensor.SensorType', *args, **kwargs):
        if sensor_type == TouchSensor.SensorType.DIGIT:
            return DigitViewer(sensor)
        elif sensor_type == TouchSensor.SensorType.GELSIGHT_MINI:
            return GelsightMiniViewer(sensor)
        else:
            raise ValueError(f'Invalid sensor type {sensor_type}')
