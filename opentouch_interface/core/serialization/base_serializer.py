from abc import ABC
import struct


def serialize(stream_name: str):
    """Decorator to register a serialization function for a specific data stream."""

    def decorator(func):
        func._stream_name = stream_name
        func._is_serializer = True  # Mark as serializer
        return func

    return decorator


def deserialize(stream_name: str):
    """Decorator to register a deserialization function for a specific data stream.

    The deserialize(bin_data) must yield the original data from the binary data that serialize(data) produced.
    """

    def decorator(func):
        func._stream_name = stream_name
        func._is_deserializer = True  # Mark as deserializer
        return func

    return decorator


class BaseSerializer(ABC):
    """Abstract base class for all sensor serializers.

    This version removes the sensor_type from the metadata. The metadata now includes:
      - [Stream Name (32 bytes)] and [Timestamp (float64)]
    Total header size: 32 + 8 = 40 bytes.
    """

    def __init__(self) -> None:
        self.serializers = {}  # Maps stream name -> serialization function
        self.deserializers = {}  # Maps stream name -> deserialization function

        # Auto-register methods decorated with @serialize and @deserialize.
        for method_name in dir(self):
            method = getattr(self, method_name)
            if callable(method):
                if hasattr(method, "_is_serializer") and hasattr(method, "_stream_name"):
                    stream_name = getattr(method, "_stream_name")
                    self.serializers[stream_name] = method
                elif hasattr(method, "_is_deserializer") and hasattr(method, "_stream_name"):
                    stream_name = getattr(method, "_stream_name")
                    self.deserializers[stream_name] = method

    def serialize(self, stream_name: str, data, time_delta: float) -> bytes:
        """
        Encodes sensor data into binary format with metadata.

        Metadata format now:
          - [Stream Name (32 bytes, UTF-8, padded with nulls)]
          - [Timestamp (float64)]
        Total header size: 32 + 8 = 40 bytes.

        :param stream_name: The name of the data stream.
        :param data: The sensor data to serialize.
        :param time_delta: The timestamp (or time delta) to include.
        :return: A bytes object with metadata + serialized data.
        """
        if stream_name not in self.serializers:
            raise ValueError(f"Unknown data source: {stream_name}")

        # Serialize raw data using the appropriate function.
        serialized_data = self.serializers[stream_name](data)

        # Build metadata: stream name and time_delta.
        metadata = struct.pack(
            "32s d",
            stream_name.ljust(32, '\0').encode("utf-8"),
            time_delta
        )
        return metadata + serialized_data

    def deserialize(self, binary_data: bytes):
        """
        Decodes binary data back to its original format.

        Expects the binary data to start with a 40-byte header:
          - 32 bytes: stream name (UTF-8, padded with nulls)
          - 8 bytes: timestamp (float64)
        The remainder is the serialized content.

        :param binary_data: The full binary data (header + serialized payload).
        :return: A dictionary with keys "delta" (timestamp) and "data" (the deserialized data).
        """
        # Unpack the 40-byte header.
        stream_name, time_delta = struct.unpack("32s d", binary_data[:40])
        stream_name = stream_name.decode().strip("\0")

        # Look up the correct deserializer.
        if stream_name not in self.deserializers:
            raise ValueError(f"Unknown data source: {stream_name}")

        # Extract the payload.
        serialized_data = binary_data[40:]
        deserialized_data = self.deserializers[stream_name](serialized_data)
        return {"delta": time_delta, "data": deserialized_data}
