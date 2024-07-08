import streamlit as st

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
