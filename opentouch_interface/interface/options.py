from enum import Enum


class SetOptions(Enum):
    RESOLUTION = "resolution"
    FPS = "fps"
    INTENSITY = "intensity"
    INTENSITY_RGB = "intensity_rgb"


class Streams(Enum):
    FRAME = "frame"
