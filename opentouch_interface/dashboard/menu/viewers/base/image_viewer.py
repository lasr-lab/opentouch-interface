from abc import abstractmethod, ABC

from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.interface.touch_sensor import TouchSensor


class BaseImageViewer(ABC):
    """
    Abstract base class for viewers.
    """
    def __init__(self, sensor: TouchSensor):
        self.sensor: TouchSensor = sensor
        self.dg = None
        self.left = None
        self.right = None
        self.container = None
        self.title = None
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
