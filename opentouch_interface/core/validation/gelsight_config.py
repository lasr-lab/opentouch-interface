from typing import Union
from pydantic import BaseModel, Field, model_validator
from opentouch_interface.core.dataclasses.options import DataStream


class GelsightConfig(BaseModel, arbitrary_types_allowed=True):
    """
    A configuration model for the GelSight Mini sensor.

    This model handles the configuration for a GelSight Mini sensor, allowing
    users to set parameters like the sensor name, stream type, sampling frequency,
    and recording frequency.
    """

    sensor_name: str
    """The name of the sensor."""
    sensor_type: str = Field(default="GELSIGHT_MINI", literal=True,
                             description="Sensor type (must be 'GELSIGHT_MINI').")
    """The type of the sensor, defaults to 'GELSIGHT_MINI'."""
    stream: Union[str, DataStream] = Field(DataStream.FRAME, description="Stream type, must be 'FRAME'.")
    """The stream type, must be 'FRAME', defaults to 'FRAME'."""
    sampling_frequency: int = Field(30, description="Sampling frequency in Hz, defaults to 30 Hz.")
    """The sampling frequency in Hz, defaults to 30 Hz."""
    recording_frequency: int = Field(0, description="Recording frequency in Hz. Defaults to sampling_frequency "
                                                    "if set to 0.")
    """The recording frequency in Hz, defaults to the sampling frequency (30 Hz if not specified)."""

    @model_validator(mode='after')
    def validate_model(self):
        """
        Validator method to ensure the correct values for certain fields after model initialization.

        This validates the stream type and ensures that the recording frequency defaults
        to the sampling frequency if not explicitly set.
        """
        # Validate stream type
        if not isinstance(self.stream, DataStream):
            if not isinstance(self.stream, str) or self.stream != "FRAME":
                raise ValueError(f"Invalid stream '{self.stream}': Stream must be a string set to 'FRAME'.")
            self.stream = DataStream.FRAME

        # Ensure recording_frequency defaults to sampling_frequency if it's not provided or invalid
        if self.recording_frequency <= 0:
            self.recording_frequency = self.sampling_frequency

        return self
