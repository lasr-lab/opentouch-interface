import os
import re

from opentouch_interface.core.registries.class_registries import ConfigClassRegistry, WidgetConfigRegistry
from opentouch_interface.core.sensor_group import CentralRegistry


class GroupNameValidator:
    def __init__(self, group_name: str | None) -> None:
        self.group_name = group_name or f'Group {len(CentralRegistry.sensor_group_registry().sensor_groups)}'


class SourceValidator:
    def __init__(self, source: str | None, method: str) -> None:
        # The source is only relevant when in replay mode (which is the case when 'method' is set to 'dataset').
        # It is the relative path to the base directory from where the dataset is being replayed.

        if method == 'dataset':
            if source is None:
                raise ValueError('Source must be specified')

            if any(source == s.source for s in CentralRegistry.sensor_group_registry().sensor_groups):
                raise ValueError('Only one group may read from a dataset at once')

            # When loading a dataset whose group hasn't been unloaded
            # - 'Hardware Group' is pointing with its 'destination' to the same file as
            # - 'Replay Group' with its 'source'
            # Therefore, when loading a dataset, check if its 'source' is some other group's 'destination'
            if any(source == s.destination for s in CentralRegistry.sensor_group_registry().sensor_groups):
                raise ValueError('Only one group may read from a dataset at once. This is probably caused by having '
                                 'the group used for recording still loaded and pointing to the same dataset.')

        self.source = source or ''


class DestinationValidator:
    def __init__(self, destination: str | None) -> None:
        """
        The 'destination' is the relative path to the base directory where data will be stored when recording.

        The following rules apply:
            - The destination must contain letters, numbers and underscores only
            - The absolute destination (base directory + destination) must not already exist
            - The destination must not already be taken by some other group
            - The final destination must end with '.touch'

        If the provided destination does not fulfill all the rules, the next best name is generated automatically.
        """
        destination = destination or 'recording'

        # Step 1: Strip and normalize whitespace
        destination = re.sub(r'\s+', ' ', destination).strip()
        destination = destination.replace(' ', '_')

        # Step 2: Remove any non-word characters *except* periods
        destination = re.sub(r'[^\w.]', '', destination)

        # Step 3: Ensure the name ends with '.touch' properly
        if destination.endswith(".touch"):
            base_name = destination[:-6]  # strip '.touch' for processing
        else:
            # Strip any existing extension and add '.touch' later
            base_name = re.sub(r'\.[^.]+$', '', destination)

        # Step 4: Check if there's a numeric suffix
        match = re.match(r'^(.*?)(?:_(\d+))?$', base_name)
        if match and match.group(2):
            base = match.group(1)
            current = int(match.group(2))
        else:
            base = base_name
            current = None

        name = base_name
        group_destinations = [group.destination for group in CentralRegistry.sensor_group_registry().sensor_groups]

        # Step 5: Uniqueness checks with .touch suffix
        if current is not None:
            while os.path.exists(os.path.join("datasets", name + ".touch")) or (name + ".touch") in group_destinations:
                current += 1
                name = f"{base}_{current}"
        else:
            # Candidate has no numerical suffix; append one if necessary.
            counter = 1
            while os.path.exists(os.path.join("datasets", name + ".touch")) or (name + ".touch") in group_destinations:
                name = f"{base}_{counter}"
                counter += 1

        # Final destination name with .touch suffix
        self.destination = name + ".touch"


class SensorConfigValidator:
    def __init__(self, sensor_configs: list | dict | None, method: str) -> None:
        if not isinstance(sensor_configs, list) or not sensor_configs:
            raise ValueError("Sensor configs must be a non-empty list of dictionaries.")

        if any(not isinstance(sensor, dict) for sensor in sensor_configs):
            raise ValueError("All items in sensor configs must be dictionaries.")

        if len(sensor_configs) != len({sensor.get("sensor_name") for sensor in sensor_configs}):
            raise ValueError("Sensor names must be unique within the group.")

        self.sensor_configs = []
        for sensor_dict in sensor_configs:
            sensor_type = sensor_dict.get("sensor_type")
            sensor_name = sensor_dict.get("sensor_name")

            # Set replay mode for datasets exclusively
            sensor_dict['replay_mode'] = method == 'dataset'

            if not isinstance(sensor_type, str) or not isinstance(sensor_name, str):
                raise ValueError("Each sensor must have 'sensor_type' and 'sensor_name' as strings.")

            config_cls = ConfigClassRegistry.get_config(sensor_type)
            if not config_cls:
                raise ValueError(f"Unsupported sensor type: {sensor_type}")

            self.sensor_configs.append(config_cls(**sensor_dict))


class PayloadValidator:
    def __init__(self, payload: list[dict] | None = None) -> None:
        if payload is not None and not isinstance(payload, list):
            raise ValueError("Payload must be a list or None.")

        self.payload = []
        for element_config in (payload or []):
            if not isinstance(element_config, dict):
                raise ValueError("All elements in the payload must be dictionaries.")

            element_type = element_config.get("type")
            if not isinstance(element_type, str):
                raise ValueError("Each payload element must have a 'type' key with a string value.")

            config_cls = WidgetConfigRegistry.get_config(element_type)
            if not config_cls:
                raise ValueError(f"Invalid element type '{element_type}'")

            self.payload.append(config_cls(**element_config).model_dump())


class ConfigValidator:
    def __init__(self, config: dict):
        # Case 1: config['_method'] = 'form'
        #   - The config was created using a form. Therefore, it is a single sensor and not a group.
        #   - No replay mode
        # Case 2: config['_method'] = 'dataset'
        #   - The config comes from a dataset.
        #   - It should be a group.
        #   - Replay mode is mandatory.
        # Case 3: config['_method'] = 'upload'
        #   - Config was uploaded and modified.
        #   - Can be either a single sensor or a group.
        #   - No replay mode.

        method = config.pop('_method', 'unknown')
        self.validated_config = self.validate_dict(config, method)

    @staticmethod
    def validate_dict(config: dict, method: str) -> dict:
        # A validated group config must have the following structure:
        #   - group_name: <some name>
        #   - source: <name of the directory>
        #   - destination: <name of the directory where data will be stored>
        #   - sensors: <list of sensors>
        #   - payload: <list of payload>

        # Check the structure of the yaml_config dictionary
        if 'sensor_type' in config and 'sensors' in config:
            raise ValueError("Invalid configuration: Config cannot contain both 'sensor_type' and 'sensors' keys.")

        elif 'sensor_type' not in config and 'sensors' not in config:
            raise ValueError("Invalid configuration: Config must contain either 'sensor_type' or 'sensors' key.")

        result = dict()
        result['group_name'] = GroupNameValidator(config.pop('group_name', None)).group_name
        result['source'] = SourceValidator(config.pop('source', None), method).source
        result['destination'] = DestinationValidator(config.pop('destination', None)).destination
        result['payload'] = PayloadValidator(config.pop('payload', None)).payload

        # Assume it's just a single sensor without a group
        if 'sensor_type' in config:
            result['sensors'] = SensorConfigValidator([config], method).sensor_configs

        # Assume it's a group with multiple sensors
        if 'sensors' in config:
            result['sensors'] = SensorConfigValidator(config.pop('sensors', None), method).sensor_configs

        return result
