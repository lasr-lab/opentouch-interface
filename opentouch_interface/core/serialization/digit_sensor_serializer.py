import struct

import numpy as np

from opentouch_interface.core.registries.class_registries import SerializerClassRegistry
from opentouch_interface.core.serialization.base_serializer import BaseSerializer, serialize, deserialize


@SerializerClassRegistry.register('Digit')
class DigitSensorSerializer(BaseSerializer):
    """Serializer for the Digit sensor (camera-based touch sensor)."""

    def __init__(self):
        super().__init__()

    @serialize('camera')
    def serialize_camera(self, frame: np.ndarray) -> bytes:
        """Serializes an OpenCV image as raw bytes + metadata."""
        height, width, channels = frame.shape
        metadata = struct.pack('III', height, width, channels)  # Store shape as metadata
        return metadata + frame.tobytes()

    @deserialize('camera')
    def deserialize_camera(self, binary_data: bytes) -> np.ndarray:
        """Deserializes raw OpenCV image from binary."""
        height, width, channels = struct.unpack('III', binary_data[:12])
        image_data = binary_data[12:]
        return np.frombuffer(image_data, dtype=np.uint8).reshape((height, width, channels))
