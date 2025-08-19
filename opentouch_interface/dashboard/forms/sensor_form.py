# Only used when entering the sensor config via input fields
from typing import Any


class SensorAttribute:
    def __init__(self, value: Any, required: bool):
        self.value = value
        self.required = required


class SensorForm:
    def __init__(self, attributes: dict[str, SensorAttribute] = None):
        """
        Initialize the form with a dictionary of attributes.
        Each attribute is a key-value pair where the key is the field name,
        and the value is a SensorAttribute instance.
        """
        self.attributes = attributes or {}

        # Automatically add the sensor_type attribute based on the class attribute
        if hasattr(self, "sensor_type"):
            self.add_attribute("sensor_type", self.sensor_type, required=True)

    def is_filled(self) -> bool:
        """
        Check if all required attributes have values.
        """
        return all(attr.value is not None for attr in self.attributes.values() if attr.required)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert attributes to a dictionary, only including non-None values.
        """
        return {key: attr.value for key, attr in self.attributes.items() if attr.value is not None}

    def add_attribute(self, name: str, value: Any, required: bool = False):
        """
        Dynamically add an attribute to the form.
        """
        self.attributes[name] = SensorAttribute(value, required)

    @staticmethod
    def render():
        raise NotImplementedError("render() must be implemented in subclass.")
