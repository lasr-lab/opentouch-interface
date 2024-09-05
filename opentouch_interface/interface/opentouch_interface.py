from opentouch_interface.interface.dataclasses.validation.sensors.digit_config import DigitConfig
from opentouch_interface.interface.dataclasses.validation.sensors.file_config import FileConfig
from opentouch_interface.interface.dataclasses.validation.sensors.gelsight_config import GelsightConfig
from opentouch_interface.interface.dataclasses.validation.sensors.sensor_config import SensorConfig
from opentouch_interface.interface.sensors.file_sensor import FileSensor


class OpentouchInterface:

    def __new__(cls, config: SensorConfig, *args, **kwargs):

        if isinstance(config, DigitConfig):
            try:
                from opentouch_interface.interface.sensors.digit import DigitSensor
                return DigitSensor(config=config)
            except ImportError as e:
                raise ImportError("DigitSensor dependencies are not installed. Please install them using 'pip install "
                                  "digit-interface'") from e

        if isinstance(config, GelsightConfig):
            try:
                from opentouch_interface.interface.sensors.gelsight_mini import GelsightMiniSensor
                return GelsightMiniSensor(config=config)
            except ImportError as e:
                raise ImportError("Gelsight Mini dependencies are not installed. Please install them using 'pip install"
                                  " gelsight@git+https://github.com/gelsightinc/gsrobotics") from e

        elif isinstance(config, FileConfig):
            return FileSensor(config=config)

        else:
            raise ValueError(f'Invalid sensor config {type(config)}')
