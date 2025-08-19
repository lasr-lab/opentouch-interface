from pydantic import BaseModel, model_validator, Field


class TouchSensorConfig(BaseModel, arbitrary_types_allowed=True):
    # Required
    sensor_name: str  # The name of the sensor
    sensor_type: str  # The type of the sensor

    # Optional
    data_streams: list[str] = Field(default=None)  # The list of active data streams

    # Attributes regarding the current mode
    replay_mode: bool = Field(default=False)

    @model_validator(mode='after')
    def validate_after(self):
        from opentouch_interface.core.sensors.touch_sensor import TouchSensor
        default_streams = TouchSensor.get_data_streams(self.sensor_type)
        if self.data_streams is None:
            self.data_streams = default_streams
        self.data_streams = list(set([item for item in self.data_streams if item in default_streams]))

        return self

    def model_dump(self, *args, **kwargs) -> dict:
        """Ensure parent fields are included in the dump."""
        config = super().model_dump(*args, **kwargs)
        del config['replay_mode']
        return config
