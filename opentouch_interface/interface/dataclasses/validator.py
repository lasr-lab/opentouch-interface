import datetime
import os
from io import StringIO
from typing import List, Dict, Any, Optional, Union

import h5py
import streamlit as st
import yaml
from pydantic import BaseModel, Field, model_validator
from streamlit.runtime.uploaded_file_manager import UploadedFile

from opentouch_interface.interface.sensors.digit import DigitConfig


class SliderConfig(BaseModel):
    type: str = Field(default="slider", const=True)
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
    type: str = Field(default="text_input", const=True)
    """Type of the user input. Set to "text_input" for text input."""
    label: str = Field(description='Description which will be displayed to the user. Should be unique.')
    """Description which will be displayed to the user. Should be unique."""
    default: str = Field(default="", description='Default value of the text input when first rendering, default to an '
                                                 'empty string.')
    """Default value of the text input when first rendering, default to an empty string."""


class PayloadConfig(BaseModel):
    __root__: List[Union[SliderConfig, TextInputConfig]] = Field(default_factory=list, description='User input for '
                                                                                                   'data annotation.')


class GroupConfig(BaseModel):
    group_name: str = Field(description='Name of the group. Should be unique.')
    """Name of the group. Should be unique."""
    path: Optional[str] = Field(default=None, description='Path to the hdf5 file.')
    """Path to the hdf5 file."""
    sensors: List[DigitConfig] = Field(default_factory=list, description='List of sensors.')
    """List of sensors."""
    payload: PayloadConfig = Field(default=PayloadConfig(), description='User input for data annotation.')
    """User input for data annotation."""

    @model_validator(mode='after')
    def validate_model(self):

        # Validate path
        if self.path is None:
            self.path = f"{self.sensor_type}-{self.sensor_name}-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.h5"
        if not self.path.endswith('.h5'):
            raise ValueError(f"Invalid path '{self.path}': Path must have a .h5 extension")
        if os.path.exists(self.path):
            raise ValueError(f"File '{self.path}' already exists")


class ConfigModel(BaseModel):
    group: List[GroupConfig]


class Validator:
    def __init__(self, file: UploadedFile):
        self.file: UploadedFile = file

        # TODO: Check if validation still works now that the group yaml has no group attribute anymore
        self.group_name: str = f'Group {st.session_state.group_registry.group_count()}'
        self.path: Optional[str] = None
        self.sensors: List[Dict[str, Any]] = []
        self.payload: List[Dict[str, Any]] = []

    def validate(self) -> (str, Optional[str], List[Dict[str, Any]], List[Dict[str, Any]]):

        if self.file:
            if self.file.name.endswith((".yaml", ".yml")):
                self._validate_yaml()
            elif self.file.name.endswith(".h5"):
                self._validate_h5()

        # If using the dashboard, recording must be activated manually
        for sensor in self.sensors:
            sensor['recording'] = False

        return self.group_name, self.path, self.sensors, self.payload

    def _validate_yaml(self) -> None:
        """
        Validate YAML file input (are used when uploading config files)
        """
        config: BaseModel = ConfigModel(**yaml.safe_load(StringIO(self.file.getvalue().decode("utf-8"))))

        # Check if the config file contains a group or just a single sensor
        if 'group' in dict_config:
            dict_config: List[Dict[str, Any]] = dict_config['group']

            for item in dict_config:
                if 'group_name' in item:
                    self.group_name = item['group_name']
                elif 'sensors' in item:
                    self.sensors = item['sensors']
                elif 'payload' in item:
                    self.payload = item['payload']
                elif 'path' in item:
                    self.path = item['path']

    def _validate_h5(self) -> None:
        """
        Validate h5 file input (are used when uploading recorded data)
        """

        with h5py.File(self.file, 'r') as hf:
            if 'payload' in hf.attrs:
                self.payload = hf.attrs['payload']

            for sensor_name in hf.keys():
                group = hf[sensor_name]
                config = group['config']

                for dataset_name in group:
                    dataset = group[dataset_name]
