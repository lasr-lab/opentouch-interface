from typing import Union

from opentouch_interface.interface.dataclasses.validation.sensors.digit_config import DigitConfig
from opentouch_interface.interface.dataclasses.validation.sensors.file_config import FileConfig
from opentouch_interface.interface.touch_sensor import TouchSensor
from opentouch_interface.interface.sensors.file_sensor import FileSensor


class OpentouchInterface:

    def __new__(cls, config: Union[DigitConfig, FileConfig], *args, **kwargs):

        sensor_type: TouchSensor.SensorType = TouchSensor.SensorType[config.sensor_type]

        if sensor_type == TouchSensor.SensorType.DIGIT:
            try:
                from opentouch_interface.interface.sensors.digit import DigitSensor
                return DigitSensor(config=config)
            except ImportError as e:
                raise ImportError("DigitSensor dependencies are not installed. Please install them using 'pip install "
                                  "digit-interface'") from e

        # elif sensor_type == TouchSensor.SensorType.GELSIGHT_MINI:
        #     try:
        #         from opentouch_interface.interface.sensors.gelsight_mini import GelsightMiniSensor
        #         return GelsightMiniSensor()
        #     except ImportError as e:
        #         raise ImportError("GelsightMiniSensor dependencies are not installed. Please install them using 'pip "
        #                           "install git+ssh://git@github.com/gelsightinc/gsrobotics.git'") from e

        elif sensor_type == TouchSensor.SensorType.FILE:
            return FileSensor(config=config)

        else:
            raise ValueError(f'Invalid sensor type {sensor_type}')
