from typing import Union, List
from pydantic import BaseModel, Field, model_validator

from opentouch_interface.interface.options import DataStream
from opentouch_interface.interface.dataclasses.image.image import Image


class FileConfig(BaseModel, validate_assignment=True, arbitrary_types_allowed=True):
    """A configuration model for the File sensor."""

    sensor_name: str
    """The name of the sensor"""
    sensor_type: str = Field(default="FILE", literal=True, description="Sensor type (must be 'FILE')")
    """The type of the sensor, defaults to 'FILE'"""
    frames: List[Image] = Field(default_factory=list)
    """List to store frames, defaults to an empty list"""
    current_frame_index: int = Field(default=0)
    """Index of the current frame, defaults to 0"""
    stream: Union[str, DataStream] = Field(DataStream.FRAME, description="Stream type (FRAME)")
    '''The stream type, must be "FRAME", defaults to "FRAME"'''
    recording_frequency: int = Field(escription="Recording frequency in Hz")
    '''The frequency in Hz at which the data was recorded'''

    @model_validator(mode='after')
    def validate_model(self):
        # Validate stream
        if not isinstance(self.stream, DataStream):
            if not isinstance(self.stream, str) or self.stream != "FRAME":
                raise ValueError(f"Invalid stream '{self.stream}': Stream must be a str set to 'FRAME'")
            self.stream: DataStream = DataStream.FRAME
