from opentouch_interface.dashboard.menu.sensor_viewer import SensorViewer

import streamlit as st

st.title('Opentouch Viewer')
st.divider()

if 'viewers' not in st.session_state or len(st.session_state.viewers) == 0:
    st.info(
        body="Once you've added new sensors through the 'Add Sensor' page, their live data will be displayed here.",
        icon="💡"
    )

sensor_viewer = SensorViewer()
sensor_viewer.render_settings()
sensor_viewer.render_data()
