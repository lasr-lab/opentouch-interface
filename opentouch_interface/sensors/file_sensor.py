from typing import Any
from opentouch_interface.options import SetOptions, Streams
from opentouch_interface.touch_sensor import TouchSensor
from opentouch_interface.dataclasses.image import Image, ImageReader
import cv2


class FileSensor(TouchSensor):

    def __init__(self, sensor_type: TouchSensor.SensorType):
        super().__init__(sensor_type)
        self.sensor = None
        self.frames = []
        self.current_frame_index = 0
        self.settings = {}

    def initialize(self, name: str, serial: str, path: str) -> ImageReader:
        reader = ImageReader(file_path=path)
        self.sensor = reader
        self.frames = self.sensor.read_from_file()

        self.settings["Name"] = name
        self.settings["File path"] = serial
        self.settings["path"] = path
        return self.sensor

    def connect(self):
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

    def disconnect(self):
        pass
