# This class is based on Meta's Digit project (https://github.com/facebookresearch/digit-interface),
# which is licensed under the Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) license.
# Please ensure compliance with the license terms when using or modifying this code.

import logging

import cv2
import numpy as np
import pyudev

logger = logging.getLogger(__name__)


class DigitHandler:
    @staticmethod
    def _parse_device(digit_dev: dict[str, str]) -> dict[str, str]:
        """Parse a single udev device's details into a dictionary."""
        return {
            "dev_name": digit_dev["DEVNAME"],
            "manufacturer": digit_dev["ID_VENDOR"],
            "model": digit_dev["ID_MODEL"],
            "revision": digit_dev["ID_REVISION"],
            "serial": digit_dev["ID_SERIAL_SHORT"],
        }

    @staticmethod
    def list_digits() -> list[dict[str, str]]:
        """List all connected DIGIT devices based on udev device information."""
        context = pyudev.Context()
        logger.debug("Finding udev devices with subsystem=video4linux, id_model=DIGIT")
        digits = context.list_devices(subsystem="video4linux", ID_MODEL="DIGIT")

        parsed_devices = [DigitHandler._parse_device(device) for device in digits]

        if not parsed_devices:
            logger.debug("No DIGIT devices found.")

        return parsed_devices

    @staticmethod
    def find_digit(serial: str) -> dict[str, str] | None:
        """Find a DIGIT device by its serial number."""
        devices = DigitHandler.list_digits()
        logger.debug(f"Searching for DIGIT with serial number {serial}")

        for device in devices:
            if device["serial"] == serial:
                return device

        logger.error(f"No DIGIT device with serial number {serial} found.")
        return None


class DigitDefaults:
    STREAMS: dict = {
        "VGA": {
            "resolution": {"width": 640, "height": 480},
            "fps": {"30fps": 30, "15fps": 15},
        },
        "QVGA": {
            "resolution": {"width": 320, "height": 240},
            "fps": {"60fps": 60, "30fps": 30},
        },
    }
    LIGHTING_MIN: int = 0
    LIGHTING_MAX: int = 15


class Digit(DigitDefaults):
    __LIGHTING_SCALER = 17

    def __init__(self, serial: str = None, name: str = None) -> None:
        """Initialize the Digit class for managing a single DIGIT device."""
        self.serial: str = serial
        self.name: str = name
        self.__dev: cv2.VideoCapture | None = None

        self.dev_name: str = ""
        self.manufacturer: str = ""
        self.model: str = ""
        self.revision: int = 0

        self.resolution: dict = {}
        self.fps: int = 0
        self.intensity: int = 0

        if self.serial is not None:
            logger.debug(f"Digit object constructed with serial {self.serial}")
            digit = DigitHandler.find_digit(serial)
            if digit is None:
                raise Exception(f"Cannot find DIGIT with serial {self.serial}")

            self.dev_name = digit["dev_name"]
            self.manufacturer = digit["manufacturer"]
            self.model = digit["model"]
            self.revision = int(digit["revision"])
            self.serial = digit["serial"]

    def connect(self) -> None:
        """Connect to the DIGIT device and set default configurations."""
        self.__dev = cv2.VideoCapture(self.dev_name)
        if not self.__dev.isOpened():
            logger.error(f"Cannot open video capture device {self.serial} - {self.dev_name}")
            raise Exception(f"Error opening video stream: {self.dev_name}")

        self.set_resolution(self.STREAMS["QVGA"])
        self.set_fps(self.STREAMS["QVGA"]["fps"]["60fps"])
        self.set_intensity(self.LIGHTING_MAX)

    def set_resolution(self, resolution: dict) -> None:
        """Set the video stream resolution."""
        self.resolution = resolution["resolution"]
        width, height = resolution["resolution"]["width"], resolution["resolution"]["height"]
        self.__dev.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.__dev.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        logger.debug(f"{self.serial}: Stream resolution set to {width}x{height}")

    def set_fps(self, fps: int) -> None:
        """Set the video stream frame rate."""
        self.fps = fps
        self.__dev.set(cv2.CAP_PROP_FPS, fps)
        logger.debug(f"{self.serial}: Stream FPS set to {fps}")

    def set_intensity(self, intensity: int) -> int:
        """Set the LED intensity"""
        # Deprecated version 1.01 (1b) is not supported
        if self.revision < 200:
            intensity = int(intensity / self.__LIGHTING_SCALER)
            logger.warning("Update firmware to support independent RGB control.")

        return self.set_intensity_rgb(intensity, intensity, intensity)

    def set_intensity_rgb(self, intensity_r: int, intensity_g: int, intensity_b: int) -> int:
        """Set LED intensity for each color channel."""
        if not all(0 <= x <= 15 for x in (intensity_r, intensity_g, intensity_b)):
            raise ValueError("RGB values must be between 0 and 15.")

        self.intensity = (intensity_r << 8) | (intensity_g << 4) | intensity_b
        self.__dev.set(cv2.CAP_PROP_ZOOM, self.intensity)
        logger.debug(f"{self.serial}: LED intensity set (R: {intensity_r}, G: {intensity_g}, B: {intensity_b})")
        return self.intensity

    def get_frame(self, max_retries: int = 3) -> np.ndarray | None:
        """Retrieve a single frame from the device."""
        for retry in range(max_retries):
            ret, frame = self.__dev.read()
            if ret:
                frame = cv2.transpose(frame)
                frame = cv2.flip(frame, 0)
                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Try reconnecting the camera
            if self.__dev:
                self.__dev.release()
            self.__dev = cv2.VideoCapture(self.serial) if self.serial is not None else None

            logger.error(f"Frame retrieval failed (Attempt {retry + 1}/{max_retries}).")

        logger.error(f"Failed to retrieve frame after {max_retries} attempts.")
        return None

    def save_frame(self, path: str) -> None:
        """Save the current frame to the specified path."""
        frame = self.get_frame()
        if frame is not None:
            cv2.imwrite(path, frame)
            logger.debug(f"Frame saved to {path}")

    def get_diff(self, ref_frame: np.ndarray) -> np.ndarray:
        """Compute the difference between the current frame and a reference frame."""
        current_frame = self.get_frame()
        return current_frame - ref_frame if current_frame is not None else None

    def show_view(self, ref_frame: np.ndarray = None) -> None:
        """Display a live view from the DIGIT device."""
        while True:
            frame = self.get_frame()
            if ref_frame is not None:
                frame = self.get_diff(ref_frame)

            cv2.imshow(f"Digit View {self.serial}", frame)
            if cv2.waitKey(1) == 27:  # ESC key
                break

        cv2.destroyAllWindows()

    def disconnect(self) -> None:
        """Disconnect the device and release resources."""
        if self.__dev:
            self.__dev.release()
            logger.debug(f"{self.serial}: Device disconnected.")

    def __repr__(self) -> str:
        return f"Digit(serial={self.serial}, name={self.name})"
