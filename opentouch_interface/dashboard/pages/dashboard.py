import streamlit as st

from opentouch_interface.dashboard.util.key_generator import UniqueKeyGenerator
from opentouch_interface.interface.dataclasses.group_registry import GroupRegistry

# Crete a GroupRegistry in session state
if 'group_registry' not in st.session_state:
    st.session_state.group_registry = GroupRegistry()

if 'key_generator' not in st.session_state:
    st.session_state.key_generator = UniqueKeyGenerator()

st.set_page_config(
    page_title="Opentouch Viewer",
    page_icon="👌",
    initial_sidebar_state="expanded",
)

add_sensor = st.Page(
    page="add_sensor.py",
    title="Add Sensor",
    icon="➕"
)

live_view = st.Page(
    page="live_view.py",
    title="Live View",
    icon="📈"
)

pg = st.navigation(
    {
        "Sensor Management": [add_sensor, live_view]
    }
)

pg.run()
