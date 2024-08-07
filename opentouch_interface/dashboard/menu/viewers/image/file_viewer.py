import os
import random
from typing import List

import h5py
from streamlit.delta_generator import DeltaGenerator
import streamlit as st

from opentouch_interface.dashboard.menu.viewers.base.image_viewer import BaseImageViewer
from opentouch_interface.interface.options import DataStream
from opentouch_interface.interface.touch_sensor import TouchSensor


class FileViewer(BaseImageViewer):
    def __init__(self, sensor: TouchSensor):
        # Load payload from .h5 file
        super().__init__(sensor=sensor, payload=sensor.sensor.get_payload())

        for element in self.payload:
            element["key"] = random.random()

        self.sensor_names = self.sensor.sensor.get_sensor_names()
        self.image_widgets = []

    def render_options(self):
        """
        Render options specific to the Digit sensor.
        """
        sensor_name = self.sensor.config.sensor_name

        # Render heading with sensor name
        self.right.markdown(f"## Settings for {sensor_name}")

        self.right.button(
            label="Restart video",
            on_click=self.restart_videos(),
            type="secondary"
        )

    def restart_videos(self):
        for sensor_name in self.sensor_names:
            self.sensor.sensor.restart(sensor_name=sensor_name)

    def get_frame(self, sensor_name: str):
        """
        Get the current frame from the sensor.
        """

        frame = self.sensor.read(DataStream.FRAME, sensor_name=sensor_name)
        if frame is not None:
            return frame.as_cv2()
        return None

    def update_delta_generator(self, dg: DeltaGenerator):
        """
        Update the delta generator for rendering frames.
        """
        self.container = dg.container(border=True)
        self.title = self.container.empty()
        self.left, self.right = self.container.columns(2)
        self.dg = dg
        self.image_widgets = [self.left.image([]) for _ in range(len(self.sensor_names))]
        self.payload_title = self.container.empty()

    def render_frame(self):
        """
        Render the current frame to the image widget.
        """

        for index, sensor_name in enumerate(self.sensor_names):
            frame = self.get_frame(sensor_name=sensor_name)

            if frame is not None and self.image_widgets[index] is not None:
                self.image_widgets[index].image(frame)

    def render_payload(self):
        if self.payload is None or not isinstance(self.payload, List):
            return

        self.payload_title.markdown(f"### Payload for sensor '{self.sensor.config.sensor_name}'")

        with self.container:
            for element in self.payload:
                element_type = element['type']

                if element_type == "slider":
                    st.slider(
                        label=element.get("label", "Some slider input"),
                        min_value=element.get("min_value", 0),
                        max_value=element.get("max_value", 100),
                        value=element.get("current_value", 0),
                        step=1,
                        label_visibility="visible",
                        key=element["key"],
                    )

                elif element_type == "text_input":
                    st.text_input(
                        label=element.get("label", "Some text input"),
                        value=element.get("current_value", ""),
                        label_visibility="visible",
                        key=element["key"],
                    )

            st.button(
                label="Save changes",
                type="primary",
                disabled=False,
                on_click=self.persist_payload,
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
