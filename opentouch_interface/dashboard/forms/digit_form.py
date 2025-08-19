import pyudev

from opentouch_interface.core.registries.class_registries import SensorFormRegistry
from opentouch_interface.dashboard.forms.sensor_form import SensorForm
import streamlit as st


@SensorFormRegistry.register_form('Digit')
class DigitForm(SensorForm):

    @staticmethod
    def _list_connected_digits() -> list[str]:
        """
        Returns a list of serial ids for all connected digit sensors.
        """
        context = pyudev.Context()
        digits = context.list_devices(subsystem="video4linux", ID_MODEL="DIGIT")

        # Extract the serial from each parsed digit device
        connected_digits = [device.get("ID_SERIAL_SHORT") for device in digits]

        return list(set(connected_digits))

    def render(self) -> SensorForm:
        serial_id = st.selectbox(
            label="Select Digit's serial number",
            options=DigitForm._list_connected_digits(),
            label_visibility="visible"
        )
        sensor_name = st.text_input(
            label="Enter Digit's name",
            value="Finger",
            placeholder="Sensor name (e.g., Thumb)",
            label_visibility="visible"
        )
        sensor_path = st.text_input(
            label="Where should Digit save its data?",
            value=None,
            placeholder="Name for a new dataset when recording (optional)",
            label_visibility="visible"
        )

        # Add attributes dynamically
        self.add_attribute("sensor_name", sensor_name, required=True)
        self.add_attribute("serial_id", serial_id, required=True)
        self.add_attribute("destination", sensor_path, required=False)

        return self
