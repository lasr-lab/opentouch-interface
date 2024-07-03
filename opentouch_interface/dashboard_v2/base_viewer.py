from abc import abstractmethod, ABC

import streamlit as st
from opentouch_interface.interface.touch_sensor import TouchSensor


class BaseViewer(ABC):
    """
    Abstract base class for viewers.
    """
    def __init__(self, sensor: TouchSensor):
        self.sensor: TouchSensor = sensor
        self.container = st.container(border=True)
        self.left, self.right = self.container.columns(2)

    @abstractmethod
    def render_left(self):
        pass

    @abstractmethod
    def render_right(self):
        pass
