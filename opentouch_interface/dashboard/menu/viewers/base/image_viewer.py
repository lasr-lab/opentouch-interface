from abc import abstractmethod, ABC
from typing import List

from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.interface.touch_sensor import TouchSensor


class BaseImageViewer(ABC):
    """
    Abstract base class for viewers.
    """
    def __init__(self, sensor: TouchSensor, payload: List):
        self.sensor: TouchSensor = sensor
        self.payload = payload
        self.dg = None
        self.left = None
        self.right = None
        self.container = None
        self.title = None
        self.payload_title = None
        self.group = "all"

    @abstractmethod
    def render_options(self):
        pass

    @abstractmethod
    def update_delta_generator(self, dg: DeltaGenerator):
        """
        Update the delta generator for rendering frames.
        """

    @abstractmethod
    def render_frame(self):
        """
        Render the current frame to the image widget.
        """

    @abstractmethod
    def render_payload(self):
        pass

    @abstractmethod
    def persist_payload(self):
        pass
