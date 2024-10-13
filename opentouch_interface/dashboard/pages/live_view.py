from opentouch_interface.dashboard.viewers.group_registry import GroupRegistryRenderer
import streamlit as st

# Initialize the GroupRegistryRenderer to handle the display of sensor data.
group_registry_renderer = GroupRegistryRenderer()

# Check if there are no viewers (i.e., sensors) in the current group registry session.
if st.session_state.group_registry.viewer_count() == 0:
    st.info(
        body="Once you've added new sensors through the 'Add Sensor' page, their live data will be displayed here.",
        icon="💡"
    )

# Render the group registry which will display the live sensor data if available.
group_registry_renderer.render()
