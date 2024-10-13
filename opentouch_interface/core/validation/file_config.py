from typing import Union, List
from pydantic import BaseModel, Field, model_validator
from opentouch_interface.core.dataclasses.options import DataStream
from opentouch_interface.core.dataclasses.image.image import Image


class FileConfig(BaseModel, validate_assignment=True, arbitrary_types_allowed=True):
    """
    A configuration model for the File sensor.

    This model defines the configuration required for handling a File sensor,
    including the sensor name, type, frames, and related attributes.
    """

    sensor_name: str
    """The name of the sensor."""
    sensor_type: str = Field(default="FILE", literal=True, description="Sensor type (must be 'FILE').")
    """The type of the sensor, defaults to 'FILE'."""
    frames: List[Image] = Field(default_factory=list, description="List of frames, defaults to an empty list.")
    """A list to store the frames for the sensor, defaults to an empty list."""
    current_frame_index: int = Field(default=0, description="Index of the current frame, defaults to 0.")
    """The index of the current frame being processed, defaults to 0."""
    stream: Union[str, DataStream] = Field(DataStream.FRAME, description="Stream type, defaults to 'FRAME'.")
    """The stream type for the sensor, must be 'FRAME', defaults to 'FRAME'."""
    recording_frequency: int = Field(..., description="Recording frequency in Hz.")
    """The frequency in Hz at which the data was recorded."""

    @model_validator(mode='after')
    def validate_model(self):
        """
        Validator method to ensure the correct values for certain fields after model initialization.

        It validates the stream type, ensuring it is either 'FRAME' or a valid `DataStream` instance.
        """
        # Validate stream
        if not isinstance(self.stream, DataStream):
            if not isinstance(self.stream, str) or self.stream != "FRAME":
                raise ValueError(f"Invalid stream '{self.stream}': Stream must be a str set to 'FRAME'.")
            self.stream = DataStream.FRAME

        return self
