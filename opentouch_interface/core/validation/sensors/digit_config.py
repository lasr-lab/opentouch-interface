import warnings
from pydantic import Field, conint, conlist

from opentouch_interface.core.registries.class_registries import ConfigClassRegistry
from opentouch_interface.core.validation.touch_sensor_config import TouchSensorConfig


@ConfigClassRegistry.register_config('Digit')
class DigitConfig(TouchSensorConfig):
    # Required
    serial_id: str  # The serial ID of the sensor

    # Optional
    rgb: conlist(conint(ge=0, le=15), min_length=3, max_length=3) = Field(default=[15, 15, 15])  # RGB values (0-15).
    resolution: str = Field('QVGA', pattern='^(VGA|QVGA)$')  # Resolution (either VGA or QVGA)

    def set_fps(self, fps: int) -> None:
        if fps not in [30, 60]:
            warnings.warn(f"Invalid fps '{fps}': FPS must be either 30 or 60.")

        # Adjust resolution based on FPS
        self.resolution = "VGA" if fps == 30 else "QVGA"
