from enum import Enum


class SensorSettings(Enum):
    SENSOR_NAME = "sensor_name"
    SERIAL_ID = "serial_id"
    MANUFACTURER = "manufacturer"
    RESOLUTION = "resolution"
    FPS = "fps"
    INTENSITY = "intensity"
    INTENSITY_RGB = "intensity_rgb"
    PATH = "path"
    CALIBRATION = "calibration"
    CURRENT_FRAME_INDEX = "current_frame_index"


class DataStream(Enum):
    FRAME = "frame"
