from abc import abstractmethod

from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.options import Streams
from opentouch_interface.touch_sensor import TouchSensor


class Viewer:
    def __init__(self, sensor: TouchSensor):
        self.sensor: TouchSensor = sensor
        self.image_widget = None
        self.dg = None
        self.left = None
        self.right = None

    @abstractmethod
    def render_options(self):
        pass

    def get_frame(self):
        return self.sensor.read(Streams.FRAME).as_cv2()

    def update_delta_generator(self, dg: DeltaGenerator, left: DeltaGenerator, right: DeltaGenerator):
        self.dg = dg
        self.left = left
        self.right = right
        self.image_widget = self.left.image([])

    def render_frame(self):
        frame = self.get_frame()
        self.image_widget.image(frame)
