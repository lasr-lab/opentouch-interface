from typing import Union
from pydantic import BaseModel, Field, PrivateAttr, model_validator
from opentouch_interface.core.dataclasses.options import DataStream
from opentouch_interface.core.dataclasses.image.image import Image


class DigitConfig(BaseModel, arbitrary_types_allowed=True):
    """
    A configuration model for the DIGIT sensor.

    This model is used to configure various parameters for the DIGIT sensor, including
    frame rate (fps), resolution, intensity, stream type, and more. It also handles validation
    of the configuration and sets certain values implicitly based on others (e.g., fps and resolution).
    """

    sensor_name: str
    """The name of the sensor."""
    sensor_type: str = Field(default="DIGIT", literal=True, description="Sensor type (must be 'DIGIT').")
    """The type of the sensor, defaults to 'DIGIT'."""
    serial_id: str
    """The serial ID of the sensor."""
    manufacturer: str = Field(default="Not specified", description="The manufacturer of the sensor.")
    """The manufacturer of the sensor, defaults to 'Not specified'."""
    fps: int = Field(60, description="Frame rate (must be 30 or 60).")
    """The frame rate, must be either 30 or 60, defaults to 60."""
    intensity: int = Field(15, ge=0, le=15, description="Intensity level (0-15).")
    """The intensity level, ranges from 0 to 15, defaults to 15."""
    resolution: str = Field('QVGA', pattern='^(VGA|QVGA)$', description="Resolution (must be 'VGA' or 'QVGA').")
    """The resolution, either 'VGA' or 'QVGA', defaults to 'QVGA'."""
    stream: Union[str, DataStream] = Field(DataStream.FRAME, description="Stream type (must be 'FRAME').")
    """The stream type, must be 'FRAME', defaults to 'FRAME'."""
    _calibration: Image = PrivateAttr(default=None)
    """Private attribute to store the calibration image, defaults to None."""
    sampling_frequency: int = Field(30, description="Sampling frequency in Hz.")
    """The sampling frequency in Hz, defaults to 30 Hz."""
    recording_frequency: int = Field(0, description="Recording frequency in Hz (defaults to sampling frequency).")
    """The recording frequency in Hz, defaults to 30 Hz."""

    @model_validator(mode='after')
    def validate_model(self):
        """
        Validator method to ensure that the model has valid values for fps, resolution,
        and stream type. It also sets the recording frequency if it's not provided.
        """
        # Validate fps
        if self.fps not in [30, 60]:
            raise ValueError(f"Invalid fps '{self.fps}': FPS must be either 30 or 60.")

        # Validate stream
        if not isinstance(self.stream, DataStream):
            if not isinstance(self.stream, str) or self.stream != "FRAME":
                raise ValueError(f"Invalid stream '{self.stream}': Stream must be a str set to 'FRAME'.")
            self.stream: DataStream = DataStream.FRAME

        # Validate fps and resolution together
        if (self.fps == 30 and self.resolution != "VGA") or (self.fps == 60 and self.resolution != "QVGA"):
            raise ValueError(
                f"Invalid fps and resolution combination: FPS of {self.fps} requires resolution "
                f"'{'VGA' if self.fps == 30 else 'QVGA'}' but found '{self.resolution}' instead."
            )

        # Set recording_frequency to sampling_frequency if not set
        if self.recording_frequency <= 0:
            self.recording_frequency = self.sampling_frequency

        return self

    def set_fps(self, fps: int) -> None:
        """
        Set the frames per second (FPS) and implicitly adjust the resolution.

        :param fps: Frame rate to set (must be 30 or 60).
        :raises ValueError: If the provided FPS is not 30 or 60.
        """
        if fps not in [30, 60]:
            raise ValueError(f"Invalid fps '{fps}': FPS must be either 30 or 60.")

        # Adjust resolution based on FPS
        self.resolution = "VGA" if fps == 30 else "QVGA"
        self.fps = fps

    def set_resolution(self, resolution: str) -> None:
        """
        Set the resolution and implicitly adjust the frames per second (FPS).

        :param resolution: Resolution to set (must be 'VGA' or 'QVGA').
        :raises ValueError: If the provided resolution is not 'VGA' or 'QVGA'.
        """
        if resolution not in ["VGA", "QVGA"]:
            raise ValueError(f"Invalid resolution '{resolution}': Resolution must be either 'VGA' or 'QVGA'.")

        # Adjust FPS based on resolution
        self.fps = 30 if resolution == "VGA" else 60
        self.resolution = resolution
