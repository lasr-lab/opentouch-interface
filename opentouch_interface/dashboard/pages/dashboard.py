import streamlit as st

st.set_page_config(
    page_title="Opentouch Viewer",
    page_icon="👌",
    initial_sidebar_state="expanded",
    layout="wide"
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

add_model = st.Page(
    page="add_model.py",
    title="Add Model",
    icon="🧠"
)

model_view = st.Page(
    page="model_view.py",
    title="Model View",
    icon="🧠"
)

pg = st.navigation(
    {
        "Sensor Management": [add_sensor, live_view],
        "Model Management": [add_model, model_view]
    }
)

# Run the navigation interface to allow switching between pages
pg.run()
