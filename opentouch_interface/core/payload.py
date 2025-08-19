from opentouch_interface.core.validation.validator import PayloadValidator


class Payload:
    def __init__(self, payload: list[dict]):
        self._config: list[dict] = payload

    def add(self, config: dict):
        # Validate the config using PayloadValidator
        try:
            validated_config = PayloadValidator(payload=[config]).payload[0]
        except Exception as e:
            raise ValueError(f"Invalid configuration: {e}")

        # Check for duplicate labels
        if any(validated_config['label'] == elem['label'] for elem in self._config):
            raise ValueError(f"The label '{validated_config['label']}' already exists.")

        self._config.append(validated_config)

    def remove(self, label: str):
        self._config = [elem for elem in self._config if elem['label'] != label]

    @property
    def is_empty(self):
        return not self._config

    def to_list(self):
        return self._config
