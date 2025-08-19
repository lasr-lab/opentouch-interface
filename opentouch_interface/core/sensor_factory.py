from opentouch_interface.core.registries.class_registries import SensorClassRegistry
from opentouch_interface.core.validation.sensor_config import SensorConfig


class SensorFactory:
    """
    Factory class to create sensor instances based on the provided configuration.
    """

    def __new__(cls, config: SensorConfig, *args, **kwargs):
        """
        Creates a new sensor instance based on the provided configuration.
        """

        # Extract sensor type from provided config
        sensor_type = getattr(config, "sensor_type", None)
        if sensor_type is None:
            # Should never get raised as this attribute is added automatically once registered
            raise ValueError(f"Configuration must define 'sensor_type': {config}")

        # Retrieve the corresponding sensor class from the registry
        sensor_cls = SensorClassRegistry.get_sensor(sensor_type)
        if sensor_cls is None:
            raise ValueError(f"Unsupported sensor type: {sensor_type} is not a registered sensor class")

        return sensor_cls(config, *args, **kwargs)
