import streamlit as st

from opentouch_interface.dashboard.menu.sensor_registry import SensorRegistry
from opentouch_interface.interface.dataclasses.group_registry import GroupRegistry

st.title('Opentouch Viewer')

# Crete a GroupRegistry in session state
if 'group_registry' not in st.session_state:
    st.session_state.group_registry = GroupRegistry()

sensor_registry = SensorRegistry()
sensor_registry.show()
