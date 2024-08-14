import streamlit as st

from opentouch_interface.dashboard.menu.sensor_registry import SensorRegistry

st.title('Opentouch Viewer')

sensor_registry = SensorRegistry()
sensor_registry.show()
