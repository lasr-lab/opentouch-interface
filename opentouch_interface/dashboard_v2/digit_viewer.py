from opentouch_interface.dashboard_v2.base_viewer import BaseViewer
from opentouch_interface.interface.options import Streams, SetOptions

import streamlit as st


class DigitViewer(BaseViewer):
    def render_left(self):
        image_widget = self.left.image([])
        with self.left:
            while True:
                frame = self.get_frame()
                image_widget.image(frame)

    def render_right(self):
        with self.right:
            self.right.markdown(f"## Settings for {self.sensor.settings['Name']}")
            resolution = st.selectbox("Resolution", ("QVGA", "VGA"),
                                              key=f"Resolution_{self.sensor.settings['Name']}")
            fps = st.selectbox("FPS", ("30", "60"), key=f"FPS_{self.sensor.settings['Name']}")
            intensity = st.slider("Brightness", 0, 15, 15, key=f"Brightness_{self.sensor.settings['Name']}")

            self.sensor.set(SetOptions.INTENSITY, value=int(intensity))
            self.sensor.set(SetOptions.RESOLUTION, value=resolution)
            self.sensor.set(SetOptions.FPS, value=int(fps))

    def get_frame(self):
        return self.sensor.read(Streams.FRAME).as_cv2()
