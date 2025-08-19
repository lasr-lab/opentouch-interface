from opentouch_interface.core.validation.sensors.digit360_config import Digit360Config
from opentouch_interface.core.validation.sensors.digit_config import DigitConfig
from opentouch_interface.core.validation.sensors.gelsight_config import GelSightConfig

# Unified sensor configuration type
SensorConfig = DigitConfig | GelSightConfig | Digit360Config
