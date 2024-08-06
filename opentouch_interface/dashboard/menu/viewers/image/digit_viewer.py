import os
import random
from typing import List

import h5py
from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.dashboard.menu.viewers.base.image_viewer import BaseImageViewer
from opentouch_interface.interface.options import SensorSettings, DataStream
from opentouch_interface.interface.touch_sensor import TouchSensor

import streamlit as st


class DigitViewer(BaseImageViewer):
    def __init__(self, sensor: TouchSensor, payload: List):
        super().__init__(sensor=sensor, payload=payload)
        self.image_widget = None

        self.sensor_name: str = self.sensor.config.sensor_name
        self.streams_key: str = f"streams_{self.sensor_name}"
        self.brightness_key: str = f"brightness_{self.sensor_name}"
        self.streams_options = ("QVGA, 60 FPS", "VGA, 30 FPS")

        # Keys to store state of select-boxes and sliders in session state
        self.brightness_state = None
        self.streams_state = None

    def render_options(self):
        """
        Render options specific to the Digit sensor.
        """

        # Render heading with sensor name
        self.title.markdown(f"### Settings for sensor '{self.sensor_name}'")

        # Check if saved state already is in session state
        if self.brightness_state is None:
            self.brightness_state = self.sensor.get(SensorSettings.INTENSITY)
            st.session_state[self.brightness_key] = self.brightness_state
        else:
            st.session_state[self.brightness_key] = self.brightness_state

        if self.streams_state is None:
            self.streams_state = (f"{self.sensor.get(SensorSettings.RESOLUTION)}, "
                                  f"{self.sensor.get(SensorSettings.FPS)} FPS")
            st.session_state[self.streams_key] = self.streams_state
        else:
            st.session_state[self.streams_key] = self.streams_state

        # Render resolution and slider selection
        self.right.selectbox(
            label="Resolution",
            options=self.streams_options,
            on_change=self.update_resolution,
            key=self.streams_key,
            disabled=st.session_state['recording_state']
        )

        self.right.slider(
            label="Brightness",
            min_value=0,
            max_value=15,
            value=15,
            on_change=self.update_fps,
            key=self.brightness_key,
            disabled=st.session_state['recording_state']
        )

    def update_fps(self):
        self.brightness_state = st.session_state[self.brightness_key]
        self.sensor.set(SensorSettings.INTENSITY, value=int(st.session_state[self.brightness_key]))

    def update_resolution(self):
        self.streams_state = st.session_state[self.streams_key]

        # Parse selected resolution and FPS
        resolution, fps = self.streams_state.split(", ")
        fps = int(fps.split()[0])

        self.sensor.set(SensorSettings.RESOLUTION, value=resolution)
        self.sensor.set(SensorSettings.FPS, value=fps)

    def update_delta_generator(self, dg: DeltaGenerator):
        """
        Update the delta generator for rendering frames.
        """
        self.container = dg.container(border=True)
        self.title = self.container.empty()
        self.left, self.right = self.container.columns(2)
        self.dg = dg
        self.image_widget = self.left.image([])
        self.payload_title = self.container.empty()

    def render_frame(self):
        """
        Render the current frame to the image widget.
        """

        def get_frame():
            """
            Get the current frame from the sensor.
            """
            data = self.sensor.read(DataStream.FRAME)
            if data is not None:
                return data.as_cv2()
            return None

        frame = get_frame()
        if frame is not None and self.image_widget is not None:
            self.image_widget.image(frame)

    def render_payload(self):
        if self.payload is None:
            return

        self.payload_title.markdown(f"### Payload for sensor '{self.sensor_name}'")

        with self.container:
            for element in self.payload:
                element_type = element['type']

                if "key" not in element:
                    element["key"] = random.random()

                if element_type == "slider":
                    st.slider(
                        label=element.get("label", "Some slider input"),
                        min_value=element.get("min_value", 0),
                        max_value=element.get("max_value", 100),
                        value=element.get("default", 0),
                        step=1,
                        label_visibility="visible",
                        key=element["key"],
                    )

                elif element_type == "text_input":
                    st.text_input(
                        label=element.get("label", "Some text input"),
                        value=element.get("default", ""),
                        label_visibility="visible",
                        key=element["key"],
                    )

    def persist_payload(self):
        # Update payload
        for element in self.payload:
            key = element["key"]

            if key in st.session_state:
                element["current_value"] = st.session_state[key]

        # Save payload to disk
        path = self.sensor.config.path
        if os.path.exists(path):
            with h5py.File(path, 'r+') as hf:
                hf.attrs['payload'] = str(self.payload)
