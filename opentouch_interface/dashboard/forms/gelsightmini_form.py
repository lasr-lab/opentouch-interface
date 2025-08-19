import streamlit as st

from opentouch_interface.core.registries.class_registries import SensorFormRegistry
from opentouch_interface.dashboard.forms.sensor_form import SensorForm


@SensorFormRegistry.register_form('GelSight Mini')
class GelSightMiniForm(SensorForm):

    def render(self) -> SensorForm:
        sensor_name = st.text_input(
            label="Enter GelSightMini's name",
            value="Finger",
            placeholder="Sensor name (e.g., Thumb)",
            label_visibility="visible"
        )
        sensor_path = st.text_input(
            label="Where should GelSightMini save its data?",
            value=None,
            placeholder="Name for a new dataset when recording (optional)",
            label_visibility="visible"
        )

        # Add attributes dynamically
        self.add_attribute("sensor_name", sensor_name, required=True)
        self.add_attribute("destination", sensor_path, required=False)

        return self
