from pydantic import BaseModel, Field, model_validator
from opentouch_interface.core.registries.class_registries import WidgetConfigRegistry


@WidgetConfigRegistry.register_widget('slider')
class SliderConfig(BaseModel):
    """
    Slider widget configuration.
    """
    type: str = Field(default='slider', description='Widget type')
    label: str = Field(description='Short description')
    min_value: float = Field(default=0.0, description='Defaults to 0')
    max_value: float = Field(default=10.0, description='Defaults to 10')
    step: float = Field(default=1.0, description='Defaults to 1')
    default: float = Field(default=0.0, description='Defaults to 0')

    @model_validator(mode='after')
    def validate_model(self):
        if self.default < self.min_value:
            self.default = self.min_value
        elif self.default > self.max_value:
            self.default = self.max_value
        return self


@WidgetConfigRegistry.register_widget('text_input')
class TextInputConfig(BaseModel):
    """
    Text input widget configuration.
    """
    type: str = Field(default='text_input', description='Widget type')
    label: str = Field(description='Short description')
    default: str = Field(default="", description='Defaults to empty string')


@WidgetConfigRegistry.register_widget('checkbox')
class CheckboxConfig(BaseModel):
    """
    Checkbox widget configuration.
    """
    type: str = Field(default='checkbox', description='Widget type')
    label: str = Field(description='Short description')
    default: bool = Field(default=False, description='Defaults to False')


@WidgetConfigRegistry.register_widget('multiselect')
class MultiselectConfig(BaseModel):
    """
    Multiselect widget configuration.
    """
    type: str = Field(default='multiselect', description='Widget type')
    label: str = Field(description='Short description')
    options: list[str] = Field(default=[], description='Comma separated list')
    default: list[str] = Field(default=[], description='Subset of options')

    @model_validator(mode='after')
    def validate_model(self):
        self.default = [option for option in self.default if option in self.options]
        return self


@WidgetConfigRegistry.register_widget('radio')
class RadioConfig(BaseModel):
    """
    Radio button widget configuration.
    """
    type: str = Field(default='radio', description='Widget type')
    label: str = Field(description='Short description')
    options: list[str] = Field(default=[], description='Comma separated list')
    default: str | None = Field(default=None, description='Defaults to first element')
    horizontal: bool = Field(default=True, description='Defaults to horizontal')

    @model_validator(mode='after')
    def validate_model(self):
        if not self.options:
            self.options = []
        if self.default is None or self.default not in self.options:
            self.default = self.options[0] if self.options else None
        return self


@WidgetConfigRegistry.register_widget('selectbox')
class SelectboxConfig(BaseModel):
    """
    Selectbox widget configuration.
    """
    type: str = Field(default='selectbox', description='Widget type')
    label: str = Field(description='Short description')
    options: list[str] = Field(default=[], description='Comma separated list')
    default: str | None = Field(default=None, description='Defaults to first element')

    @model_validator(mode='after')
    def validate_model(self):
        if not self.options:
            self.options = []
        if self.default is None or self.default not in self.options:
            self.default = self.options[0] if self.options else None
        return self


@WidgetConfigRegistry.register_widget('number_input')
class NumberInputConfig(BaseModel):
    """
    Number input widget configuration.
    """
    type: str = Field(default='number_input', description='Widget type')
    label: str = Field(description='Short description')
    min_value: float = Field(default=0.0, description='Defaults to 0')
    max_value: float = Field(default=100.0, description='Defaults to 100')
    step: float = Field(default=1.0, description='Defaults to 1')
    default: float = Field(default=0.0, description='Defaults to min_value')

    @model_validator(mode='after')
    def validate_model(self):
        if self.default < self.min_value:
            self.default = self.min_value
        elif self.default > self.max_value:
            self.default = self.max_value
        return self
