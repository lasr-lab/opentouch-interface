from enum import Enum


class SensorSettings(Enum):
    """
    An enumeration representing various settings related to a sensor.

    Each setting corresponds to a specific attribute or configuration of the sensor.
    """
    SENSOR_NAME = "sensor_name"  # The name of the sensor
    SERIAL_ID = "serial_id"  # The unique serial ID of the sensor
    MANUFACTURER = "manufacturer"  # The sensor's manufacturer
    RESOLUTION = "resolution"  # The resolution of the sensor
    FPS = "fps"  # Frames per second, indicating the sensor's frame rate
    INTENSITY = "intensity"  # The intensity setting for the sensor
    INTENSITY_RGB = "intensity_rgb"  # RGB intensity values for the sensor
    PATH = "path"  # Path where sensor data or files are stored
    CALIBRATION = "calibration"  # Calibration information for the sensor
    CURRENT_FRAME_INDEX = "current_frame_index"  # Index of the current frame being processed


class DataStream(Enum):
    """
    An enumeration representing types of data streams.

    Currently, it defines different types of data that can be streamed or processed from a sensor.
    """
    FRAME = "frame"  # Represents a frame in the data stream
