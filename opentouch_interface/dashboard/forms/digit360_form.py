import pyudev
import streamlit as st

from opentouch_interface.core.registries.class_registries import SensorFormRegistry
from opentouch_interface.dashboard.forms.sensor_form import SensorForm


@SensorFormRegistry.register_form('Digit360')
class Digit360Form(SensorForm):

    @staticmethod
    def _list_connected_digit360() -> list[str]:
        """
        Returns a list of serial ids for all connected digit sensors.
        """
        context = pyudev.Context()
        digit360s = context.list_devices(subsystem="usb", ID_MODEL="DIGIT360_Hub")

        connected_digit360s = list(set(device.get("ID_SERIAL_SHORT") for device in digit360s))

        return list(set(connected_digit360s))

    def render(self) -> SensorForm:
        serial_id = st.selectbox(
            label="Select Digit360's serial number",
            options=Digit360Form._list_connected_digit360(),
            label_visibility="visible"
        )
        sensor_name = st.text_input(
            label="Enter Digit360's name",
            value="Finger",
            placeholder="Sensor name (e.g., Thumb)",
            label_visibility="visible"
        )
        sensor_path = st.text_input(
            label="Where should Digit360 save its data?",
            value=None,
            placeholder="Name for a new dataset when recording (optional)",
            label_visibility="visible"
        )

        # Add attributes dynamically
        self.add_attribute("sensor_name", sensor_name, required=True)
        self.add_attribute("serial_id", serial_id, required=True)
        self.add_attribute("destination", sensor_path, required=False)

        return self
