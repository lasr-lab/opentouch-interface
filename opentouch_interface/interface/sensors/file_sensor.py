import pprint
from typing import Any
from opentouch_interface.interface.options import SetOptions, Streams
from opentouch_interface.interface.touch_sensor import TouchSensor
from opentouch_interface.interface.dataclasses.image import Image, ImageReader
import cv2


class FileSensor(TouchSensor):
    def __init__(self):
        super().__init__(TouchSensor.SensorType.FILE)
        self.sensor = None
        self.frames = []
        self.current_frame_index = 0
        self.settings = {}

    def initialize(self, name: str, serial: str, path: str) -> None:
        self.sensor = ImageReader(file_path=path)
        self.frames = self.sensor.get_all()

        self.settings["Name"] = name
        self.settings["File path"] = serial
        self.settings["path"] = path

    def connect(self):
        pass

    def calibrate(self, num_frames: int = 100, skip_frames: int = 20) -> None:
        pass

    def set(self, attr: SetOptions, value: Any) -> Any:
        self.settings[attr] = value

    def get(self, attr: SetOptions) -> Any:
        return self.settings.get(attr)

    def read(self, attr: Streams, value: Any = None) -> Image:
        if attr == Streams.FRAME and self.frames and self.current_frame_index < len(self.frames):
            frame = self.frames[self.current_frame_index]
            self.current_frame_index += 1
            return frame

        else:
            raise ValueError("attr did not match any available attribute.")

    def show(self, attr: Streams, recording: bool = False) -> Any:
        if attr == Streams.FRAME:
            delay = 1 / self.sensor.fps  # Calculate the delay between frames for the specified FPS

            while self.current_frame_index < len(self.frames):
                frame = self.read(Streams.FRAME)
                if frame is not None:
                    cv2.imshow('Frame', frame.as_cv2())
                    if cv2.waitKey(int(delay * 1000)) & 0xFF == ord('q'):
                        break
                else:
                    break
            cv2.destroyAllWindows()

    def info(self, verbose: bool = True):
        if verbose:
            pprint.pprint(self.settings)

        return self.settings

    def disconnect(self):
        pass
