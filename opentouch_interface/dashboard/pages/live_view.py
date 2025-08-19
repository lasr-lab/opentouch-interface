from opentouch_interface.core.registries.central_registry import CentralRegistry
import streamlit as st

# Check if there are no viewers (i.e., sensors) in the current group registry session.
if not CentralRegistry.viewer_group_registry().group_count:
    st.info(
        body="Once you've added new sensors through the 'Add Sensor' page, their live data will be displayed here.",
        icon="💡"
    )

# Render the group registry which will display the live sensor data if available.
CentralRegistry.viewer_group_registry().render()
