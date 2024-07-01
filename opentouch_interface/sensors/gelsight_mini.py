import pprint
import time
import warnings
from typing import Any

import cv2
import numpy as np

from opentouch_interface.dataclasses.image import ImageWriter, Image
from opentouch_interface.options import SetOptions, Streams
from opentouch_interface.touch_sensor import TouchSensor
from gelsight import gsdevice


class GelsightMiniSensor(TouchSensor):
    def __init__(self):
        super().__init__(TouchSensor.SensorType.GELSIGHT_MINI)
        self.gelsight = None
        self.name = None
        self.device_type = "GelSight Mini"

    def initialize(self, name: str, serial: None, path: str) -> None:
        if serial is not None:
            raise ValueError("GelSight Mini does not expect a serial ID")

        self.name = name
        self.settings["Name"] = name
        self.settings["path"] = path
        self.gelsight = gsdevice.Camera(dev_type=self.device_type)

    def connect(self) -> None:
        self.gelsight.connect()

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

    def set(self, attr: SetOptions, value: Any = None) -> Any:
        if value is not None:
            warnings.warn("attr did not match any available attribute. Skipped this case")

    def get(self, attr: SetOptions) -> Any:
        if attr not in self.settings:
            warnings.warn("attr did not match any available attribute. Returning None instead")
            return None

        return self.settings[attr]

    def read(self, attr: Streams, value: Any = None) -> Any:
        if attr == Streams.FRAME:
            if value is not None:
                raise TypeError(f"When reading frames, expected value must be None but found {value} instead")
            return self.gelsight.get_image()

        else:
            raise ValueError("attr did not match any available attribute.")

    def show(self, attr: Streams, recording: bool = False) -> None:
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

    def info(self, verbose: bool = True):
        if verbose:
            pprint.pprint(self.settings)

        return self.settings

    def disconnect(self):
        pass
