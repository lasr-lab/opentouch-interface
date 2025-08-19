import os
import re
import warnings

import cv2
import numpy as np


class GelSightMiniCamera:
    """
    A class to interface with the GelSight Mini camera.

    This class handles the connection, sensors capture, and disconnection for the GelSight Mini sensor.
    """

    def __init__(self):
        self._dev_id: int | None = None
        self._camera: cv2.VideoCapture | None = None

    def connect(self) -> None:
        """Attempts to find and connect to the GelSight Mini camera by searching the video devices."""
        for file in os.listdir("/sys/class/video4linux"):
            real_file = os.path.join("/sys/class/video4linux", file, "name")
            with open(real_file, "rt") as name_file:
                name = name_file.read().strip()

            if 'GelSight Mini' in name:
                self._dev_id = int(re.search(r"\d+$", file).group())

        self._camera = cv2.VideoCapture(self._dev_id)
        if not self._camera or not self._camera.isOpened():
            warnings.warn("Failed to open GelSight Mini camera device")

    def get_frame(self, max_retries=3) -> np.ndarray | None:
        """Capture a frame from the camera, crop it, and resize it to 320x240."""
        if not self._camera:
            warnings.warn("Camera not connected. Call `connect()` first.")
            return None

        retries = 0
        while retries <= max_retries:
            ret, frame = self._camera.read() if self._camera else (False, None)
            if ret and frame is not None:
                try:
                    border_x = int(frame.shape[0] * (1 / 7))
                    border_y = int(frame.shape[1] * (1 / 7))
                    cropped_frame = frame[border_x:-border_x, border_y:-border_y]
                    resized_frame = cv2.resize(cropped_frame, (320, 240))
                    return resized_frame
                except Exception as e:
                    warnings.warn(f"Error processing frame: {e}")

            if self._camera:
                self._camera.release()
            self._camera = cv2.VideoCapture(self._dev_id) if self._dev_id is not None else None

            if not self._camera or not self._camera.isOpened():
                warnings.warn("Failed to reconnect to the GelSight Mini camera.")

            retries += 1
            print(f"Reconnecting camera: attempt {retries} of {max_retries}")

        print(f"Failed to capture frame after {max_retries} retries. Returning None.")

    def disconnect(self) -> None:
        """Release the camera resource when done."""
        if self._camera:
            self._camera.release()
            self._camera = None
