from opentouch_interface.interface.sensors.digit import DigitSensor
from opentouch_interface.interface.sensors.file_sensor import FileSensor
from opentouch_interface.interface.sensors.gelsight_mini import GelsightMiniSensor
from opentouch_interface.interface.touch_sensor import TouchSensor


class OpentouchInterface:

    def __new__(cls, sensor_type: 'TouchSensor.SensorType', *args, **kwargs):
        if sensor_type == TouchSensor.SensorType.DIGIT:
            return DigitSensor()
        elif sensor_type == TouchSensor.SensorType.GELSIGHT_MINI:
            return GelsightMiniSensor()
        elif sensor_type == TouchSensor.SensorType.FILE:
            return FileSensor()
        else:
            raise ValueError(f'Invalid sensor type {sensor_type}')
