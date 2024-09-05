from abc import abstractmethod, ABC
from typing import Optional

from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.interface.touch_sensor import TouchSensor


class BaseImageViewer(ABC):
    """
    Abstract base class for viewers.
    """
    def __init__(self, sensor: TouchSensor):
        self.sensor: TouchSensor = sensor

        self.sensor_name: str = self.sensor.config.sensor_name

        self.container: Optional[DeltaGenerator] = None
        self.title: Optional[DeltaGenerator] = None
        self.left: Optional[DeltaGenerator] = None
        self.right: Optional[DeltaGenerator] = None
        self.image_widget: Optional[DeltaGenerator] = None

    @abstractmethod
    def render_options(self) -> None:
        """
        Render options of the viewer.
        """
        pass

    @abstractmethod
    def render_frame(self) -> None:
        """
        Render the current frame to the image widget.
        """
        pass

    def update_container(self, container: DeltaGenerator) -> None:
        """
        Update the container for rendering frames.
        """
        self.container = container.container(border=True)
        self.title = self.container.empty()
        self.left, self.right = self.container.columns(2)
        self.image_widget = self.left.image([])
