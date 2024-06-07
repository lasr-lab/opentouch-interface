from typing import Any, Dict, List

from opentouch_interface.options import SetOptions, Streams
from opentouch_interface.touch_sensor import TouchSensor
from digit_interface.digit import Digit


class DigitSensor(TouchSensor):

    def __init__(self):
        self.digit = None

    def initialize(self, name: str, serial: str) -> Digit:
        self.digit = Digit(serial=serial, name=name)
        return self.digit

    def connect(self):
        self.digit.connect()

    def set(self, attr: SetOptions, value: Any) -> Any:
        # Set resolution
        if attr == SetOptions.RESOLUTION:
            if isinstance(value, Dict):
                self.digit.set_resolution(value)
            else:
                raise TypeError(f"Expected value must be of type typing.Dict but found {type(value)} instead")

        # Set frame rate
        elif attr == SetOptions.FPS:
            if isinstance(value, int):
                self.digit.set_fps(value)
            else:
                raise TypeError(f"Expected value must be of type int but found {type(value)} instead")

        # Set intensity
        elif attr == SetOptions.INTENSITY:
            if isinstance(value, int):
                return self.digit.set_intensity(value)
            else:
                raise TypeError(f"Expected value must be of type int but found {type(value)} instead")

        # Set RGB intensity
        elif attr == SetOptions.INTENSITY_RGB:
            if isinstance(value, List) and len(value) == 3:
                return self.digit.set_intensity_rgb(*value)
            else:
                raise TypeError(f"Expected value must be of type typing.List with length of 3 but found "
                                f"{type(value)} with length {len(value)} instead")

        # Error case
        else:
            raise ValueError("attr did not match any available attribute.")

    def read(self, attr: Streams, value: Any = None) -> Any:
        if attr == Streams.FRAME:
            if isinstance(value, bool) or value is None:
                transpose = (value is not None) or value
                return self.digit.get_frame(transpose)
            else:
                raise TypeError(f"Expected value must be of type bool but found {type(value)} instead")

        else:
            raise ValueError("attr did not match any available attribute.")

    def show(self, attr: Streams, value: Any = None) -> Any:
        if attr == Streams.FRAME:
            self.digit.show_view()
        else:
            raise ValueError("attr did not match any available attribute.")

    def close(self):
        self.digit.disconnect()
