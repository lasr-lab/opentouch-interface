import pprint
import warnings
from typing import Any

from opentouch_interface.interface.options import SensorSettings, DataStream
from opentouch_interface.interface.touch_sensor import TouchSensor
from opentouch_interface.interface.dataclasses.image import Image, ImageReader
import cv2


class FileSensor(TouchSensor):
    def __init__(self):
        super().__init__(TouchSensor.SensorType.FILE)
        self.frames = []
        self.current_frame_index = 0
        self.settings = {}

    def initialize(self, name: str, serial: str, path: str) -> None:
        if serial is not None:
            print(type(serial))
            raise ValueError("A file sensor does not expect a serial ID")

        self.sensor = ImageReader(file_path=path)
        self.frames = self.sensor.get_all_frames()

        self.settings[SensorSettings.SENSOR_NAME] = name
        self.settings[SensorSettings.PATH] = path

    def connect(self):
        pass

    def calibrate(self, num_frames: int = 100, skip_frames: int = 20) -> None:
        pass

    def set(self, attr: SensorSettings, value: Any) -> Any:
        if not isinstance(attr, SensorSettings):
            raise TypeError(f"Expected attr to be of type SensorSettings but found {type(attr)} instead.\n")

        self.settings[attr] = value

    def get(self, attr: SensorSettings) -> Any:
        if not isinstance(attr, SensorSettings):
            raise TypeError(f"Expected attr to be of type SensorSettings but found {type(attr)} instead.\n")

        if attr not in self.settings:
            available_attributes = ", ".join(setting for setting in self.settings.keys())
            warnings.warn(f"The Digit sensor only supports the following options to be retrieved: "
                          f"{available_attributes}. The provided attribute '{attr}' did not match any of these "
                          f"options. Returning None instead.\n", stacklevel=2)
            return None

        return self.settings[attr]

    def read(self, attr: DataStream, value: Any = None) -> Image:
        if not isinstance(attr, DataStream):
            raise TypeError(f"Expected attr to be of type DataStream but found {type(attr)} instead.\n")

        if attr == DataStream.FRAME:
            if self.sensor:
                return self.sensor.get_next_frame_timed()

        else:
            warnings.warn("The provided attribute did not match any available attribute.\n")

    def show(self, attr: DataStream, recording: bool = False) -> Any:
        if not isinstance(attr, DataStream):
            raise TypeError(f"Expected attr to be of type DataStream but found {type(attr)} instead.\n")

        if attr == DataStream.FRAME:
            while True:
                frame = self.read(DataStream.FRAME)
                if frame is not None:
                    cv2.imshow('Frame', frame.as_cv2())
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                else:
                    break
            cv2.destroyAllWindows()

        else:
            warnings.warn("The provided attribute did not match any available attribute.\n", stacklevel=2)
            return None

    def info(self, verbose: bool = True):
        if verbose:
            pprint.pprint(self.settings)

        return self.settings

    def disconnect(self):
        pass
