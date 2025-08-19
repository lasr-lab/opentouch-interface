from opentouch_interface.core.sensor_group_saver import SensorGroupSaver


class Decoder:
    """
    Decoder loads and parses sensor data and configuration from a file.

    Terminology:
      - Sensor: A hardware sensor identified by a 'sensor_name'.
      - Stream: A named data channel within a sensor (e.g., "acceleration", "temperature").
      - Event: A data record in a stream, usually a dictionary with keys 'delta' (timestamp) and 'data' (value).

    Data structure:
      {
          sensor_name: {
              stream_name: [event, event, ...],
              ...
          },
          ...
      }

    Example after stripping 'delta':
      {
          "sensor_1": {
              "acceleration": [[0.1, 0.2, 9.8], [0.0, 0.1, 9.7], ...],
              "temperature": [22.5, 22.6, ...]
          },
          "sensor_2": {
              "pressure": [101.3, 101.2, ...]
          }
      }
    """

    def __init__(self, file_path: str):
        self._file_path = file_path
        self._data: dict = SensorGroupSaver.get_all_decoded_data_from_file(file_path)
        try:
            self._config: dict = SensorGroupSaver.read_config(file_path)
        except Exception as e:
            print(f"Error reading config from file {file_path}: {e}")
            self._config = {}

    @property
    def config(self) -> dict:
        """Returns the config dictionary."""
        return self._config

    @property
    def sensors(self) -> list:
        """Returns the list of sensor configs."""
        return self._config.get("sensors", [])

    @property
    def sensor_names(self) -> list:
        """Returns all sensor names."""
        return [sensor.get("sensor_name") for sensor in self.sensors if sensor.get("sensor_name")]

    @property
    def data(self) -> dict:
        """Returns decoded sensor data."""
        return self._data

    def config_of(self, sensor_name: str) -> dict:
        """Returns config for a specific sensor."""
        for sensor in self.sensors:
            if sensor.get("sensor_name") == sensor_name:
                return sensor
        return {}

    def data_of(self, sensor_name: str) -> dict:
        """Returns all decoded data for a sensor."""
        return self._data.get(sensor_name, {})

    def stream_data_of(self, sensor_name: str, stream: str, with_delta=True) -> list:
        """Returns events for a specific sensor stream."""
        sensor_data = self.data_of(sensor_name)
        if with_delta:
            return sensor_data.get(stream, [])
        return [event['data'] for event in sensor_data.get(stream, [])]

    def stream_names_of(self, sensor_name: str) -> list:
        """Returns available stream names for a sensor."""
        sensor_data = self.data_of(sensor_name)
        return list(sensor_data.keys())

    def stream_length_of(self, sensor_name: str, stream: str) -> int:
        """Returns number of events in a stream."""
        return len(self.stream_data_of(sensor_name, stream))

    @property
    def summary(self) -> dict:
        """Returns event count per sensor and stream."""
        summary = {}
        for sensor_name in self.sensor_names:
            sensor_data = self.data_of(sensor_name)
            summary[sensor_name] = {stream: len(events) for stream, events in sensor_data.items()}
        return summary

    def event_data_of(self, sensor_name: str, stream: str) -> list:
        """Returns only the 'data' part of events."""
        events = self.stream_data_of(sensor_name, stream)
        return [
            event['data'] if isinstance(event, dict) and 'data' in event else event
            for event in events
        ]

    def all_event_data(self) -> dict:
        """Returns all event data without 'delta' timestamps."""
        all_points = {}
        for sensor_name in self.sensor_names:
            sensor_data = self.data_of(sensor_name)
            if sensor_data:
                all_points[sensor_name] = {}
                for stream, events in sensor_data.items():
                    all_points[sensor_name][stream] = [
                        event['data'] if isinstance(event, dict) and 'data' in event else event
                        for event in events
                    ]
        return all_points
