from abc import abstractmethod, ABC

from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.interface.options import DataStream
from opentouch_interface.interface.touch_sensor import TouchSensor


class BaseViewer(ABC):
    """
    Abstract base class for viewers.
    """
    def __init__(self, sensor: TouchSensor):
        self.sensor: TouchSensor = sensor
        self.image_widget = None
        self.dg = None
        self.left = None
        self.right = None
        self.container = None

    @abstractmethod
    def render_options(self):
        pass

    def get_frame(self):
        """
        Get the current frame from the sensor.
        """
        return self.sensor.read(DataStream.FRAME).as_cv2()

    def update_delta_generator(self, dg: DeltaGenerator):
        """
        Update the delta generator for rendering frames.
        """
        self.container = dg.container(border=True)
        self.left, self.right = self.container.columns(2)
        self.dg = dg
        self.image_widget = self.left.image([])

    def render_frame(self):
        """
        Render the current frame to the image widget.
        """
        frame = self.get_frame()
        self.image_widget.image(frame)
