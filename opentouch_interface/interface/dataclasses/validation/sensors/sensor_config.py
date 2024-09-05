from typing import TypeAlias, Union

from opentouch_interface.interface.dataclasses.validation.sensors.digit_config import DigitConfig
from opentouch_interface.interface.dataclasses.validation.sensors.file_config import FileConfig
from opentouch_interface.interface.dataclasses.validation.sensors.gelsight_config import GelsightConfig


SensorConfig: TypeAlias = Union[DigitConfig, FileConfig, GelsightConfig]
