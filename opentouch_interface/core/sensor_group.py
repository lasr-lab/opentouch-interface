import os
import pprint
import warnings

from opentouch_interface.core.oti_config import OTIConfig
from opentouch_interface.core.registries.central_registry import CentralRegistry
from opentouch_interface.core.sensor_factory import SensorFactory
from opentouch_interface.core.sensor_group_saver import SensorGroupSaver
from opentouch_interface.core.sensors.touch_sensor import TouchSensor
from opentouch_interface.core.validation.validator import ConfigValidator, DestinationValidator


class SensorGroup:
    """
    Manages a group of sensors: loading configuration, starting/stopping recording, and handling replay.
    """

    def __init__(self, config: dict[str, str]):
        from opentouch_interface.core.payload import Payload  # Dynamic import to prevent cyclic dependency

        # Validate and parse the configuration
        config: dict = ConfigValidator(config=config).validated_config

        self._group_name: str = config['group_name']
        self._source: str = config['source']  # Relative path from which the data is read during replay mode
        self._destination: str = config['destination']  # Relative path to which the data is written when recording
        self.payload: Payload = Payload(payload=config['payload'])

        # Initialize sensors based on the configuration
        self.sensors: list[TouchSensor] = [SensorFactory(config=sensor_config) for sensor_config in config['sensors']]

        # Register this SensorGroup in the global registry
        CentralRegistry.sensor_group_registry().add(self)

        # Attributes for data recording
        self._is_recording: bool = False
        self._has_unsaved_config: bool = False
        self._saver = SensorGroupSaver(self)

        # Start replaying data
        if self.is_replay_mode:
            self.start_replay(offset_seconds=0)

    # Class methods
    @classmethod
    def from_dataset(cls, path) -> 'SensorGroup':
        """Instantiate a sensor group given a dataset name."""

        if config := SensorGroupSaver.read_config(path):
            config['_method'] = 'dataset'
            config['source'] = path
            return cls(config)

        raise ValueError(f"Could not load configuration from {path}")

    # Properties
    @property
    def group_name(self) -> str:
        return self._group_name

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @property
    def source(self) -> str:
        """
        Returns the source of the config. This is relevant in replay mode so the
        SensorGroupSaver knows from where to load the recorded data.

        This is NOT the full path to the source but rather the relative path to the base directory.
        """
        return self._source

    @property
    def destination(self) -> str:
        """
        Returns the destination of the config. This is relevant when recording so the
        SensorGroupSaver knows where to save the recorded data.

        This is NOT the full path to the destination but rather the relative path to the base directory.
        """
        return self._destination

    @property
    def abs_source(self) -> str:
        """
        Same as self.source but with the base directory included.
        """
        return os.path.join(OTIConfig.get_base_directory(), self.source)

    @property
    def abs_destination(self) -> str:
        """
        Same as self.destination but with the base directory included.
        """
        return os.path.join(OTIConfig.get_base_directory(), self.destination)

    # Public methods
    def get_sensor(self, sensor_name: str) -> TouchSensor | None:
        """Retrieve a sensor by its name."""
        return next((sensor for sensor in self.sensors if sensor.get('sensor_name') == sensor_name), None)

    def disconnect(self):
        """Disconnect all sensors in the group if not recording."""
        if self._is_recording:
            warnings.warn("Cannot disconnect sensors while recording.", UserWarning)
            return

        self._saver.stop_replay()

        # Persist any changes made to the config
        self.update_saved_group_config()

        for sensor in self.sensors:
            sensor.disconnect()

        CentralRegistry.sensor_group_registry().remove(self)

    def get_config(self) -> dict:
        """
        Return the configuration of the sensor group.

        The 'source' isn't returned as part of the config as this is implicitly given by the name of the
        directory at ./datasets/<source>
        """

        return {
            'group_name': self.group_name,
            'destination': self.destination,
            'sensors': [sensor.info(verbose=False) for sensor in self.sensors],
            'payload': self.payload.to_list()
        }

    def info(self):
        """Provide a summary of the group configuration."""
        pprint.pprint(self.get_config())

    def start_recording(self):
        """Begin recording data from all sensors in the group."""
        if self._is_recording:
            return

        if os.path.exists(self.abs_destination):
            warnings.warn(
                f'The file {self.abs_destination} already exists. '
                f'Change the destination using SensorGroup.set_destination.',
                UserWarning
            )
            return

        self._saver.start_saving()
        self._is_recording = True

        for sensor in self.sensors:
            sensor.start_recording()

    def stop_recording(self):
        """Stop recording"""
        if not self._is_recording:
            return

        self._is_recording = False

        for sensor in self.sensors:
            sensor.stop_recording()

        self._saver.stop_saving()

        # Persist any changes made to the config
        self.update_saved_group_config()

    def set_destination(self, new_dest: str) -> bool:
        """Update the recording path if not recording."""
        if self._is_recording:
            warnings.warn("Cannot change the destination while recording.", UserWarning)
            return False

        # Persist any changes made to the config
        self.update_saved_group_config()

        self._destination = DestinationValidator(new_dest).destination
        return True

    def update_saved_group_config(self):
        """Updates an existing group configuration with the latest configuration."""

        # If the 'destination' already exists (because recording is in progress), any changes to the config should be
        # made there (./<base_dir>/<destination>)
        if os.path.isfile(self.abs_destination):
            self._saver.write_config(self.abs_destination, self.get_config())
            return

        # Write any changes while in replay mode to ./<base_dir>/<source>
        # (The only exception is when in replay mode and starting a recording from that replay. Then changes to the
        # config are again saved to the newly created recording and not the source)
        if self.is_replay_mode:
            self._saver.write_config(self.abs_source, self.get_config())

    def start_replay(self, offset_seconds: float):
        self._saver.start_replay(offset_seconds)

    @property
    def is_replay_mode(self) -> bool:
        return any(sensor.get('replay_mode') for sensor in self.sensors)

    def __repr__(self):
        return f'SensorGroup(group_name={self.group_name}, source={self.source}, destination={self.destination})'
