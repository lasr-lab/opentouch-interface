from opentouch_interface.interface.touch_sensor import TouchSensor


class OpentouchInterface:

    def __new__(cls, sensor_type: 'TouchSensor.SensorType', *args, **kwargs):
        if sensor_type == TouchSensor.SensorType.DIGIT:
            try:
                from opentouch_interface.interface.sensors.digit import DigitSensor
                return DigitSensor()
            except ImportError as e:
                raise ImportError("DigitSensor dependencies are not installed. Please install them using 'pip install "
                                  "digit-interface'") from e

        elif sensor_type == TouchSensor.SensorType.GELSIGHT_MINI:
            try:
                from opentouch_interface.interface.sensors.gelsight_mini import GelsightMiniSensor
                return GelsightMiniSensor()
            except ImportError as e:
                raise ImportError("GelsightMiniSensor dependencies are not installed. Please install them using 'pip "
                                  "install gelsight-mini-interface'") from e

        elif sensor_type == TouchSensor.SensorType.FILE:
            try:
                from opentouch_interface.interface.sensors.file_sensor import FileSensor
                return FileSensor()
            except ImportError as e:
                raise ImportError("FileSensor dependencies are not installed. Please install them using 'pip install "
                                  "file-sensor-interface'") from e

        else:
            raise ValueError(f'Invalid sensor type {sensor_type}')
