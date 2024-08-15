import ast
import datetime
import os
from io import StringIO
from typing import List, Dict, Any, Optional, Union

import h5py
import streamlit as st
import yaml
from pydantic import BaseModel, Field, model_validator, field_validator
from streamlit.runtime.uploaded_file_manager import UploadedFile

from opentouch_interface.interface.dataclasses.image.image import Image
from opentouch_interface.interface.dataclasses.validation.sensors.digit_config import DigitConfig
from opentouch_interface.interface.dataclasses.validation.sensors.file_config import FileConfig


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


class GroupNameConfig(BaseModel):
    group_name: str = Field(default=None, description='Group name, defaults to "Group <current-group-count>"')
    """Group name."""

    @field_validator('group_name', mode='before', check_fields=False)
    def set_default_group_name(cls, v):
        if v is None:
            # Access the group count from the session state
            return f'Group {st.session_state.group_registry.group_count()}'
        return v

    @model_validator(mode='after')
    def validate_model(self):
        # Make sure the group does not already exist
        group_registry = st.session_state.group_registry
        if any(group.group_name == self.group_name for group in group_registry.groups):
            raise ValueError(f"Group '{self.group_name}' already exists")
        return self


class Validator:
    def __init__(self, file: UploadedFile):
        self.file: UploadedFile = file

        self.group_name: str = ""
        self.path: str = ""
        self.sensors: List[Union[DigitConfig, FileConfig]] = []
        self.payload: List[Dict[str, Any]] = []

    def validate(self) -> (str, Optional[str], List[Union[DigitConfig, FileConfig]], List[Dict[str, Any]]):

        if self.file:
            if self.file.name.endswith((".yaml", ".yml")):
                self._validate_yaml()
            elif self.file.name.endswith(".touch"):
                self._validate_h5()

        return self.group_name, self.path, self.sensors, self.payload

    def _validate_yaml(self) -> None:
        """
        Validate YAML file input (are used when uploading config files)
        """
        yaml_config: Dict[str, Union[str, List[Dict[str, Union[str, int]]]]] = yaml.safe_load(
            StringIO(self.file.getvalue().decode("utf-8")))

        # Grab values from config
        sensors: List[Dict[str, Union[str, int]]] = yaml_config.get('sensors', [])
        payload = yaml_config.get('payload', [])

        # Validate group name and path
        self.group_name = GroupNameConfig(group_name=yaml_config.get('group_name')).group_name
        self.path = PathConfig(path=yaml_config.get('path')).path

        # Validate sensors
        if not sensors:
            raise ValueError(f"Group must contain at least one sensor.")

        for sensor_dict in sensors:
            if 'sensor_type' in sensor_dict:
                sensor_type = sensor_dict['sensor_type']
                if sensor_type == 'DIGIT':
                    self.sensors.append(DigitConfig(**sensor_dict))
                # Add more configs for other sensors here

                else:
                    raise ValueError(f"Invalid sensor type '{sensor_type}'")
            else:
                raise ValueError(f"Missing sensor type in sensors")

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
                raise ValueError(f"Missing type in payload")

    def _validate_h5(self) -> None:
        """
        Validate .touch file input (are used when uploading recorded data)
        """

        with h5py.File(self.file, 'r') as hf:
            # Check if all attributes are available
            if 'group_name' not in hf.attrs:
                raise ValueError(f"File '{self.file}' has no group name")
            if 'path' not in hf.attrs:
                raise ValueError(f"File '{self.file}' does not specify a path")
            if len(hf.keys()) == 0:
                raise ValueError(f"File '{self.file}' does not contain any sensors")

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
