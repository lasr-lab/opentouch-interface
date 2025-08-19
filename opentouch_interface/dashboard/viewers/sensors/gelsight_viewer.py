import streamlit as st

from opentouch_interface.core.registries.class_registries import ViewerClassRegistry
from opentouch_interface.core.sensors.touch_sensor import TouchSensor
from opentouch_interface.dashboard.viewers.base_viewer import BaseViewer, render


@ViewerClassRegistry.register_viewer('GelSight Mini')
class GelSightViewer(BaseViewer):

    def __init__(self, sensor: TouchSensor):
        super().__init__(sensor=sensor)
        self.image_widget = None

    @render('camera', count=1)
    def display_camera(self, data):
        """Display the camera feed in the UI."""
        if not data or not len(data['camera']):
            return

        with self.image_widget:
            st.image(data['camera'], use_container_width=True)
