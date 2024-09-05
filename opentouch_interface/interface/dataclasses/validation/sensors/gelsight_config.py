from typing import Union
from pydantic import BaseModel, Field, model_validator
from opentouch_interface.interface.options import DataStream


class GelsightConfig(BaseModel, arbitrary_types_allowed=True):
    """A configuration model for the DIGIT sensor."""

    sensor_name: str
    """The name of the sensor"""
    sensor_type: str = Field(default="GELSIGHT_MINI", literal=True, description="Sensor type (must be 'GELSIGHT_MINI')")
    '''The type of the sensor, defaults to "DIGIT"'''
    stream: Union[str, DataStream] = Field(DataStream.FRAME, description="Stream type (FRAME)")
    '''The stream type, must be "FRAME", defaults to "FRAME"'''
    sampling_frequency: int = Field(30, description="Sampling frequency in Hz")
    '''The sampling frequency in Hz, defaults to 30Hz'''
    recording_frequency: int = Field(0, description="Recording frequency in Hz")
    '''The recording frequency in Hz, defaults to sampling_frequency (which by default is 30 Hz)'''

    @model_validator(mode='after')
    def validate_model(self):

        # Validate stream
        if not isinstance(self.stream, DataStream):
            if not isinstance(self.stream, str) or self.stream != "FRAME":
                raise ValueError(f"Invalid stream '{self.stream}': Stream must be a str set to 'FRAME'")
            self.stream: DataStream = DataStream.FRAME

        # Validate recording_frequency
        if self.recording_frequency <= 0:
            self.recording_frequency = self.sampling_frequency
