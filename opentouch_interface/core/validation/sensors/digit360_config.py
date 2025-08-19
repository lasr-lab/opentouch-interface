from pydantic import Field, model_validator, conlist, conint
from pyudev import DeviceNotFoundError

from opentouch_interface.core.registries.class_registries import ConfigClassRegistry
from opentouch_interface.core.sensors.interfaces.digit360_interface import Digit360Descriptor, Digit360
from opentouch_interface.core.validation.touch_sensor_config import TouchSensorConfig

clist = conlist(conlist(conint(ge=0, le=255), min_length=3, max_length=3), min_length=8, max_length=8)


@ConfigClassRegistry.register_config('Digit360')
class Digit360Config(TouchSensorConfig):
    # Required
    serial_id: str  # The serial ID of the sensor

    # Optional
    # RGB values for the eight LEDs (defaults to (0, 0, 0) for all LEDs)
    led_values: clist = Field(default_factory=lambda: [[0, 0, 0]] * 8)

    # The descriptor is not supposed to be set by the user. This is done automatically by the interface.
    descriptor: Digit360Descriptor = Field(default=None)

    @model_validator(mode='after')
    def validate_model(self):
        # In replay mode, set descriptor to None
        if self.replay_mode:
            return self

        # Retrieve all available descriptors
        descriptors: list[Digit360Descriptor] = Digit360.get_digit360_devices()

        # Find the descriptor matching the given serial_id
        descriptor = next((d for d in descriptors if d.serial == self.serial_id), None)

        if not descriptor:
            raise DeviceNotFoundError(f"No Digit360 with serial id {self.serial_id} found.")

        # Assign the descriptor to the instance
        self.descriptor = Digit360.get_digit360_by_serial(descriptors, self.serial_id)

        return self
