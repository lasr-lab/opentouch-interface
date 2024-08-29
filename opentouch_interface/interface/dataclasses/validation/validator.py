import ast
import datetime
import os
from io import StringIO
from typing import List, Dict, Any, Optional, Union

import h5py
import yaml
from pydantic import BaseModel, Field, model_validator, field_validator
from streamlit.runtime.uploaded_file_manager import UploadedFile
import streamlit as st

from opentouch_interface.interface.dataclasses.group_registry import GroupRegistry
from opentouch_interface.interface.dataclasses.image.image import Image
from opentouch_interface.interface.dataclasses.validation.sensors.digit_config import DigitConfig
from opentouch_interface.interface.dataclasses.validation.sensors.file_config import FileConfig
from opentouch_interface.interface.dataclasses.validation.sensors.gelsight_config import GelsightConfig
from opentouch_interface.interface.dataclasses.validation.sensors.sensor_config import SensorConfig
from opentouch_interface.interface.touch_sensor import TouchSensor


class SliderConfig(BaseModel):
    type: str = Field(default="slider", Literal=True)
    """Type of the user input. Set to "slider" for slider."""
    label: str = Field(description='Description which will be displayed to the user. Should be unique.')
    """Description which will be displayed to the user. Should be unique."""
    min_value: int = Field(default=0, description='Minimum value of the slider, defaults to 0.')
    """Minimum value of the slider."""
    max_value: int = Field(default=10, description='Maximum value of the slider, defaults to 10.')
    """Maximum value of the slider."""
    default: int = Field(default=min_value, description='Default value of the slider when first rendering, default to '
                                                        '\'min_value\'.')
    """Default value of the slider when first rendering. Must be between `min_value` and `max_value`."""

    @model_validator(mode='after')
    def validate_model(self) -> None:
        if not self.min_value <= self.default <= self.max_value:
            raise ValueError(f'{self.default} must be between {self.min_value} (min_value) and {self.max_value} '
                             f'(max_value).')


class TextInputConfig(BaseModel):
    type: str = Field(default="text_input", Literal=True)
    """Type of the user input. Set to "text_input" for text input."""
    label: str = Field(description='Description which will be displayed to the user. Should be unique.')
    """Description which will be displayed to the user. Should be unique."""
    default: str = Field(default="", description='Default value of the text input when first rendering, default to an '
                                                 'empty string.')
    """Default value of the text input when first rendering, default to an empty string."""


class PathConfig(BaseModel):
    path: str = Field(default=None, description='Path to the hdf5 file, defaults to <current-time>.touch')
    """Path to the hdf5 file."""

    @field_validator('path', mode='before', check_fields=False)
    def set_default_path(cls, v):
        if v is None:
            # Access the group count from the session state
            return f'group_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.touch'
        return v

    @model_validator(mode='after')
    def validate_model(self):

        # Validate path
        self.path = f"{os.path.splitext(self.path)[0]}.touch"
        if os.path.exists(self.path):
            raise ValueError(f"File '{self.path}' already exists")


class MockGroupRegistry:
    def __init__(self):
        self.groups = []
        self._group_count = 0

    @property
    def group_count(self):
        self._group_count += 1
        return self._group_count


class SessionStateManager:
    def __init__(self):
        self.state: Optional[GroupRegistry] = getattr(st.session_state, 'group_registry', None)

    def get_group_registry(self) -> Union[GroupRegistry, MockGroupRegistry]:
        if self.state:
            return self.state
        else:
            return MockGroupRegistry()


class GroupNameConfig(BaseModel):
    group_name: str = Field(default=None, description='Group name, defaults to "Group <current-group-count>"')
    """Group name."""

    @field_validator('group_name', mode='before', check_fields=False)
    def set_default_group_name(cls, v):
        group_registry = SessionStateManager().get_group_registry()
        if v is None:
            return f'Group {group_registry.group_count}'
        return v


class Validator:
    def __init__(self, file: Union[UploadedFile, Dict]):
        self._file: Optional[UploadedFile] = file if isinstance(file, UploadedFile) else None
        self._yaml_config: Optional[Dict] = file if isinstance(file, Dict) else None

        self.group_name: str = ""
        self.path: str = ""
        self.sensors: List[SensorConfig] = []
        self.payload: List[Dict[str, Any]] = []

    def validate(self) -> (str, Optional[str], List[SensorConfig], List[Dict[str, Any]]):

        # Validate an uploaded config
        if self._file:
            if self._file.name.endswith((".yaml", ".yml")):
                self._validate_yaml()
            elif self._file.name.endswith(".touch"):
                self._validate_h5()

        # Validate manually created form
        if self._yaml_config:
            self._validate_yaml()

        return self.group_name, self.path, self.sensors, self.payload

    def _validate_yaml(self) -> None:
        """
        Validate YAML file input
        """
        # Uploaded YAML file
        if self._file:
            yaml_config: Dict[str, Union[str, List[Dict[str, Union[str, int]]]]] = yaml.safe_load(
                StringIO(self._file.getvalue().decode("utf-8")))

        # Manually created YAML file in the dashboard
        elif self._yaml_config:
            # Config comes from using code
            if 'sensor' in self._yaml_config:
                yaml_config = {
                    'sensors': [self._yaml_config['sensor']]
                }

            # Code comes from using the dashboard (manual entry and uploaded group files)
            else:
                yaml_config = self._yaml_config

        # Exit if no valid input was provided
        else:
            raise ValueError("No YAML file input")

        # Grab values from config
        sensors: List[Dict[str, Union[str, int]]] = yaml_config.get('sensors', [])
        payload = yaml_config.get('payload', [])

        # Validate group name and path
        self.group_name = GroupNameConfig(group_name=yaml_config.get('group_name')).group_name
        self.path = PathConfig(path=yaml_config.get('path')).path

        # Validate sensors
        if not sensors:
            raise ValueError("Group must contain at least one sensor.")

        if len(sensors) != len({sensor["sensor_name"] for sensor in sensors}):
            raise ValueError("Sensor names should be unique inside a group.")

        for sensor_dict in sensors:
            if 'sensor_type' in sensor_dict:
                sensor_type = sensor_dict['sensor_type']
                if sensor_type == TouchSensor.SensorType.DIGIT.name:
                    self.sensors.append(DigitConfig(**sensor_dict))
                elif sensor_type == TouchSensor.SensorType.GELSIGHT_MINI.name:
                    self.sensors.append(GelsightConfig(**sensor_dict))

                # Add more configs for other sensors here

                else:
                    raise ValueError(f"Invalid sensor type '{sensor_type}'")
            else:
                raise ValueError("Missing sensor type in sensors")

        # Validate payload
        for element_config in payload:
            if 'type' in element_config:
                element_type = element_config['type']
                if element_type == 'slider':
                    self.payload.append(SliderConfig(**element_config).dict())
                elif element_type == 'text_input':
                    self.payload.append(TextInputConfig(**element_config).dict())
                else:
                    raise ValueError(f"Invalid element type '{element_type}'")
            else:
                raise ValueError("Missing type in payload")

    def _validate_h5(self) -> None:
        """
        Validate .touch file input (are used when uploading recorded data)
        """

        with h5py.File(self._file, 'a') as hf:
            # Check if all attributes are available
            if 'group_name' not in hf.attrs:
                hf.attrs['group_name'] = 'Group 0'

                # .touch files missing a group name as well as a path is normal for files being recorded within code
                # That is because code does not support groups while 'group_name' and 'path' are both attributes that
                # belong to groups
                print(f"WARNING: File '{self._file.name}' has no group name")
            if 'path' not in hf.attrs:
                hf.attrs['path'] = self._file.name
                print(f"WARNING: File '{self._file.name}' does not specify a path")
            if len(hf.keys()) == 0:
                raise ValueError(f"File '{self._file}' does not contain any sensors")

            # Extract attributes from .touch file

            # Use GroupNameConfig here to make sure no group with the same group name is currently in use
            self.group_name = GroupNameConfig(group_name=hf.attrs['group_name']).group_name
            self.path = hf.attrs['path']

            if 'payload' in hf.attrs:
                self.payload = ast.literal_eval(hf.attrs['payload'])

            for sensor_name in hf.keys():
                group = hf[sensor_name]
                config = ast.literal_eval(group.attrs['config'])

                images: List[Image] = []
                for key in group.keys():
                    if key.startswith('image_') and key.endswith('_cv2'):
                        img_data = group[key][()]
                        images.append(Image(img_data, (0, 1, 2)))

                config['frames'] = images
                config['sensor_type'] = 'FILE'
                self.sensors.append(FileConfig(**config))
