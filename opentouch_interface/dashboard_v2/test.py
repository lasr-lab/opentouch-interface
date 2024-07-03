import streamlit as st

from opentouch_interface.dashboard_v2.digit_viewer import DigitViewer
from opentouch_interface.interface.opentouch_interface import OpentouchInterface
from opentouch_interface.interface.touch_sensor import TouchSensor

st.set_page_config(
    page_title="Opentouch Viewer",
    page_icon="👌",
    initial_sidebar_state="expanded",
)

top = st.empty()
top_divider = st.empty()

top.title('Opentouch Viewer')
top_divider.divider()


def main():
    digit = OpentouchInterface(sensor_type=TouchSensor.SensorType.DIGIT)
    digit.initialize(name="Test", serial="D20804", path="")
    digit.connect()

    digit_viewer = DigitViewer(sensor=digit)
    digit_viewer.render_right()
    digit_viewer.render_left()


if __name__ == '__main__':
    main()
