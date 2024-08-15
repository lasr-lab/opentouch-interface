from opentouch_interface.dashboard.menu.group_registry_renderer import GroupRegistryRenderer

import streamlit as st

group_registry_renderer = GroupRegistryRenderer()

if st.session_state.group_registry.viewer_count() == 0:
    st.info(
        body="Once you've added new sensors through the 'Add Sensor' page, their live data will be displayed here.",
        icon="💡"
    )

group_registry_renderer.render()
