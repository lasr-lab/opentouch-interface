import pprint
import time
from typing import Any, Dict, List

import cv2
import numpy as np

from opentouch_interface.options import SetOptions, Streams
from opentouch_interface.touch_sensor import TouchSensor
from opentouch_interface.dataclasses.image import Image, ImageWriter
from digit_interface.digit import Digit
import warnings


class DigitSensor(TouchSensor):
    def __init__(self, sensor_type: TouchSensor.SensorType):
        super().__init__(sensor_type)
        self.digit = None

    def initialize(self, name: str, serial: str, path: str) -> None:
        self.digit = Digit(serial=serial, name=name)
        self.settings["Name"] = name
        self.settings["Serial ID"] = serial
        self.settings["path"] = path

    def connect(self):
        self.digit.connect()
        self.settings[SetOptions.FPS] = self.digit.fps

    def set(self, attr: SetOptions, value: Any) -> Any:
        # Set resolution
        if attr == SetOptions.RESOLUTION:
            value_dict = Digit.STREAMS[value]
            if isinstance(value_dict, Dict):
                self.digit.set_resolution(value_dict)
                self.settings[attr] = value
            else:
                raise TypeError(f"Expected value must be of type typing.Dict but found {type(value)} instead")

        # Set frame rate
        elif attr == SetOptions.FPS:
            if isinstance(value, int):
                self.digit.set_fps(value)
                self.settings[attr] = value
            else:
                raise TypeError(f"Expected value must be of type int but found {type(value)} instead")

        # Set intensity
        elif attr == SetOptions.INTENSITY:
            if isinstance(value, int):
                self.settings[attr] = value
                return self.digit.set_intensity(value)
            else:
                raise TypeError(f"Expected value must be of type int but found {type(value)} instead")

        # Set RGB intensity
        elif attr == SetOptions.INTENSITY_RGB:
            if isinstance(value, List) and len(value) == 3:
                self.settings[attr] = value
                return self.digit.set_intensity_rgb(*value)
            else:
                raise TypeError(f"Expected value must be of type typing.List with length of 3 but found "
                                f"{type(value)} with length {len(value)} instead")

        # Error case
        else:
            warnings.warn("attr did not match any available attribute. Skipped this case")

    def get(self, attr: SetOptions) -> Any:
        if attr not in self.settings:
            warnings.warn("attr did not match any available attribute. Returning None instead")
            return None

        return self.settings[attr]

    def read(self, attr: Streams, value: Any = None) -> Any:
        if attr == Streams.FRAME:
            if isinstance(value, bool) or value is None:
                transpose = (value is not None) or value
                frame = self.digit.get_frame(transpose)
                return Image(image=frame, rotation=(0, 1, 2))
            else:
                raise TypeError(f"Expected value must be of type bool but found {type(value)} instead")

        else:
            raise ValueError("attr did not match any available attribute.")

    def show(self, attr: Streams, recording: bool = False) -> Any:
        if attr == Streams.FRAME:
            fps = self.get(attr=SetOptions.FPS)
            interval = 1.0 / fps

            with ImageWriter(file_path=self.settings["path"], fps=fps) as recorder:
                while True:
                    start_time = time.time()  # Record the start time
                    image = self.read(attr=Streams.FRAME)

                    if recording:
                        recorder.save(image)

                    cv2.imshow('Image', image.as_cv2())

                    if cv2.waitKey(1) == 27:  # Break loop if Esc key is pressed
                        break

                    elapsed_time = time.time() - start_time
                    time_to_sleep = interval - elapsed_time
                    if time_to_sleep > 0:
                        time.sleep(time_to_sleep)

            cv2.destroyAllWindows()

        else:
            raise ValueError("attr did not match any available attribute.")

    def calibrate(self, num_frames: int = 100, skip_frames: int = 20) -> Image:
        fps = self.get(SetOptions.FPS)
        if fps is None:
            raise ValueError("FPS setting must be set before calibrating.")

        interval = 1.0 / fps

        # Skip the initial frames
        for _ in range(skip_frames):
            self.read(attr=Streams.FRAME)
            time.sleep(interval)  # Sleep for the time determined by FPS

        # Collect frames after skipping
        frames = []
        for _ in range(num_frames):
            image = self.read(attr=Streams.FRAME)
            frames.append(image.as_cv2())
            time.sleep(interval)  # Sleep for the time determined by FPS

        # Calculate the average frame
        average_frame = np.mean(frames, axis=0).astype(np.uint8)
        average_image = Image(image=average_frame, rotation=(0, 1, 2))

        self.settings["calibration_reference"] = average_image

        return average_image

    def info(self, verbose: bool = True):
        if verbose:
            pprint.pprint(self.settings)

        return self.settings

    def disconnect(self):
        self.digit.disconnect()
