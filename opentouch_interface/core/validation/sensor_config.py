from typing import Union

from opentouch_interface.core.validation.digit_config import DigitConfig
from opentouch_interface.core.validation.file_config import FileConfig
from opentouch_interface.core.validation.gelsight_config import GelsightConfig

# Unified sensor configuration type
SensorConfig = Union[DigitConfig, FileConfig, GelsightConfig]
