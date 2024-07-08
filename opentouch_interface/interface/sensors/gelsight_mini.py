import pprint
import time
import warnings
from typing import Any

import cv2
import numpy as np

from opentouch_interface.interface.dataclasses.image import ImageWriter, Image
from opentouch_interface.interface.options import SensorSettings, DataStream
from opentouch_interface.interface.touch_sensor import TouchSensor
from gelsight import gsdevice


class GelsightMiniSensor(TouchSensor):
    def __init__(self):
        super().__init__(TouchSensor.SensorType.GELSIGHT_MINI)
        self.sensor = None

    def initialize(self, name: str, serial: None, path: str) -> None:
        if serial is not None:
            raise ValueError("GelSight Mini does not expect a serial ID")

        self.settings[SensorSettings.SENSOR_NAME] = name
        self.settings[SensorSettings.SERIAL_ID] = "Gelsight Mini"
        self.settings[SensorSettings.PATH] = path
        self.sensor = gsdevice.Camera(dev_type=self.settings[SensorSettings.SERIAL_ID])

    def connect(self) -> None:
        self.sensor.connect()

    def calibrate(self, num_frames: int = 100, skip_frames: int = 20) -> Image:
        fps = self.get(SensorSettings.FPS)
        if fps is None:
            raise ValueError("FPS setting must be set before calibrating.")

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

    def set(self, attr: SensorSettings, value: Any = None) -> Any:
        if not isinstance(attr, SensorSettings) or attr is not None:
            raise TypeError(f"Expected attr to be of type SensorSettings but found {type(attr)} instead.\n")

        if attr is not None:
            warnings.warn(
                "The GelsightMini sensor only supports the following options to be set: None. The provided "
                "attribute did not match any of these options and was skipped.\n",
                stacklevel=2)

    def get(self, attr: SensorSettings) -> Any:
        if not isinstance(attr, SensorSettings):
            raise TypeError(f"Expected attr to be of type SensorSettings but found {type(attr)} instead.\n")

        if attr not in self.settings:
            available_attributes = ", ".join(setting for setting in self.settings.keys())
            warnings.warn(f"The GelsightMini sensor only supports the following options to be retrieved: "
                          f"{available_attributes}. The provided attribute '{attr}' did not match any of these "
                          f"options. Returning None instead.\n", stacklevel=2)
            return None

        return self.settings[attr]

    def read(self, attr: DataStream, value: Any = None) -> Any:
        if not isinstance(attr, DataStream):
            raise TypeError(f"Expected attr to be of type DataStream but found {type(attr)} instead.\n")

        if attr == DataStream.FRAME:
            if value is not None:
                raise TypeError(f"When reading frames, expected value must be None but found {value} instead")
            return self.sensor.get_image()

        else:
            warnings.warn("The provided attribute did not match any available attribute.\n")

    def show(self, attr: DataStream, recording: bool = False) -> None:
        if attr == DataStream.FRAME:
            fps = self.get(attr=SensorSettings.FPS)
            interval = 1.0 / fps

            with ImageWriter(file_path=self.settings["path"], fps=fps) as recorder:
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

    def info(self, verbose: bool = True):
        if verbose:
            pprint.pprint(self.settings)

        return self.settings

    def disconnect(self):
        pass
