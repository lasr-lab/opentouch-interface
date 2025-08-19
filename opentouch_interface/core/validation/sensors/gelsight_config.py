from opentouch_interface.core.registries.class_registries import ConfigClassRegistry
from opentouch_interface.core.validation.touch_sensor_config import TouchSensorConfig


@ConfigClassRegistry.register_config('GelSight Mini')
class GelSightConfig(TouchSensorConfig):
    # The GelSight Mini sensor has no additional configuration parameters
    pass
