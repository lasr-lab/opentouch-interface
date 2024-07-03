import pprint
import time
from typing import Any, Dict, List

import cv2
import numpy as np

from opentouch_interface.interface.options import SensorSettings, DataStream
from opentouch_interface.interface.touch_sensor import TouchSensor
from opentouch_interface.interface.dataclasses.image import Image, ImageWriter
from digit_interface.digit import Digit
import warnings


class DigitSensor(TouchSensor):
    def __init__(self):
        super().__init__(TouchSensor.SensorType.DIGIT)
        self.sensor = None

    def initialize(self, name: str, serial: str, path: str) -> None:
        self.sensor = Digit(serial=serial, name=name)

        self.settings[SensorSettings.SENSOR_NAME] = name
        self.settings[SensorSettings.SERIAL_ID] = serial
        self.settings[SensorSettings.PATH] = path

    def connect(self):
        self.sensor.connect()

        self.settings[SensorSettings.MANUFACTURER] = self.sensor.manufacturer
        self.settings[SensorSettings.FPS] = self.sensor.fps
        self.settings[SensorSettings.RESOLUTION] = self.sensor.resolution
        self.settings[SensorSettings.INTENSITY] = self.sensor.intensity

    def set(self, attr: SensorSettings, value: Any) -> Any:
        if not isinstance(attr, SensorSettings):
            raise TypeError(f"Expected attr to be of type SensorSettings but found {type(attr)} instead.\n")

        # Set resolution
        if attr == SensorSettings.RESOLUTION:
            value_dict = Digit.STREAMS[value]
            if isinstance(value_dict, Dict):
                self.sensor.set_resolution(value_dict)
                self.settings[attr] = value
            else:
                raise TypeError(f"Expected value must be of type typing.Dict but found {type(value)} instead\n")

        # Set frame rate
        elif attr == SensorSettings.FPS:
            if isinstance(value, int):
                self.sensor.set_fps(value)
                self.settings[attr] = value
            else:
                raise TypeError(f"Expected value must be of type int but found {type(value)} instead\n")

        # Set intensity
        elif attr == SensorSettings.INTENSITY:
            if isinstance(value, int):
                self.settings[attr] = value
                return self.sensor.set_intensity(value)
            else:
                raise TypeError(f"Expected value must be of type int but found {type(value)} instead\n")

        # Set RGB intensity
        elif attr == SensorSettings.INTENSITY_RGB:
            if isinstance(value, List) and len(value) == 3:
                self.settings[attr] = value
                return self.sensor.set_intensity_rgb(*value)
            else:
                raise TypeError(f"Expected value must be of type typing.List with length of 3 but found "
                                f"{type(value)} with length {len(value) if isinstance(value, List) else 'N/A'} "
                                f"instead\n")

        # Error case
        else:
            warnings.warn("The Digit sensor only supports the following options to be set: RESOLUTION, FPS, INTENSITY, "
                          "and INTENSITY_RGB. The provided attribute did not match any of these options and was"
                          "skipped.\n", stacklevel=2)

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

    def read(self, attr: DataStream, value: Any = None) -> Any:
        if not isinstance(attr, DataStream):
            raise TypeError(f"Expected attr to be of type DataStream but found {type(attr)} instead.\n")

        if attr == DataStream.FRAME:
            if isinstance(value, bool) or value is None:
                transpose = (value is not None) or value
                frame = self.sensor.get_frame(transpose)
                return Image(image=frame, rotation=(0, 1, 2))
            else:
                raise TypeError(f"Expected value must be of type bool but found {type(value)} instead\n")

        else:
            warnings.warn("The provided attribute did not match any available attribute.\n")

    def show(self, attr: DataStream, recording: bool = False) -> Any:
        if not isinstance(attr, DataStream):
            raise TypeError(f"Expected attr to be of type DataStream but found {type(attr)} instead.\n")

        if attr == DataStream.FRAME:
            fps = self.get(attr=SensorSettings.FPS)
            interval = 1.0 / fps

            with ImageWriter(file_path=self.settings[SensorSettings.PATH], fps=fps) as recorder:
                while True:
                    start_time = time.time()  # Record the start time
                    image = self.read(attr=DataStream.FRAME)

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
            warnings.warn("The provided attribute did not match any available attribute.\n", stacklevel=2)
            return None

    def calibrate(self, num_frames: int = 100, skip_frames: int = 20) -> Image | None:
        fps = self.get(SensorSettings.FPS)
        if fps is None:
            raise ValueError("FPS setting must be set before calibrating.\n")

        interval = 1.0 / fps

        # Skip the initial frames
        for _ in range(skip_frames):
            self.read(attr=DataStream.FRAME)
            time.sleep(interval)  # Sleep for the time determined by FPS

        # Collect frames after skipping
        frames = []
        for _ in range(num_frames):
            image = self.read(attr=DataStream.FRAME)
            frames.append(image.as_cv2())
            time.sleep(interval)  # Sleep for the time determined by FPS

        # Calculate the average frame
        average_frame = np.mean(frames, axis=0).astype(np.uint8)
        average_image = Image(image=average_frame, rotation=(0, 1, 2))

        self.settings[SensorSettings.CALIBRATION] = average_image

        return average_image

    def info(self, verbose: bool = True):
        if verbose:
            pprint.pprint(self.settings)

        return self.settings

    def disconnect(self):
        self.sensor.disconnect()
