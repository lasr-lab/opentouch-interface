from collections import deque

import cv2
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
from code_editor import code_editor
from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.core.registries.class_registries import ViewerClassRegistry
from opentouch_interface.core.sensors.touch_sensor import TouchSensor
from opentouch_interface.dashboard.viewers.base_viewer import BaseViewer, render, control_sensor, control_stream


@ViewerClassRegistry.register_viewer('Digit360')
class Digit360Viewer(BaseViewer):
    def __init__(self, sensor: TouchSensor):
        super().__init__(sensor=sensor)

        # Camera
        self._image_widget = None

        # IMU
        self._imu_radio_widget = None
        self._imu_plot_widget = None

        self._imu_modes = {
            "ACC": "serial/imu/raw,sensor_=1", "GYRO": "serial/imu/raw,sensor_=2", "MAG": "serial/imu/raw,sensor_=3",
            "QUAT": "serial/imu/quat", "EULER": "serial/imu/euler", "AUX": "serial/imu/raw,sensor_=6"}
        self._imu_projections = {
            "ACC": "raw/{x,y,z}", "GYRO": "raw/{x,y,z}", "MAG": "raw/{x,y,z}", "QUAT": "quat/{x,y,z}",
            "EULER": "euler/{heading,pitch,roll}", "AUX": "raw/{x,y,z}"}

        # Pressure data
        self._pressure_radio_widget = None
        self._pressure_plot_widget = None

        self._pressure_modes = {
            "PRESSURE": "pressure/pressure", "TEMPERATURE": "pressure/temperature"}

        # GasHt data
        self._gas_radio_widget = None
        self._gas_plot_widget = None

        self._gas_modes = {
            "TEMPERATURE": "gas/temperature", "PRESSURE": "gas/pressure", "HUMIDITY": "gas/humidity", "GAS": "gas/gas"}

        # Audio
        self._audio_widget = None

        # Keys
        self._editor_key = self.state_manager.unique_key('code_editor')

    @control_sensor()
    def led_control(self):

        if self.is_recording or self.sensor.get('replay_mode'):
            # Display LED intensities (not editable)
            st.code(body=Digit360Viewer._led_values_to_string(self.sensor.get('led_values')))
        else:
            # Display menu to change LED intensity
            response = code_editor(Digit360Viewer._led_values_to_string(self.sensor.get('led_values')),
                                   key=self._editor_key)
            led_values = Digit360Viewer._string_to_led_values(response['text'])

            if led_values:
                for idx, val in enumerate(led_values):
                    self.sensor.set('led', (idx, val))

    @render('camera', projection='camera', count=1)
    def display_camera(self, data):
        """Display the camera feed in the UI."""

        if not data or 'camera' not in data:
            return  # Safely exit if data is missing or empty

        frame = data['camera'][0]

        if frame is None or not len(frame):
            return  # Ensure the frame is valid

        scale = 0.6
        h, w = frame.shape[:2]
        new_size = (int(w * scale), int(h * scale))

        resized_frame = cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)

        with self._image_widget:
            st.image(resized_frame, use_container_width=True)

    @control_stream(stream='serial')
    def pressure_selection(self):
        key = 'pressure_pills'
        self.state_manager.init_state(key, 'PRESSURE')
        with self._pressure_radio_widget:
            st.pills(label="Pressure", options=["PRESSURE", "TEMPERATURE"], selection_mode='single',
                     label_visibility='collapsed', key=self.state_manager.unique_key(key),
                     on_change=self.state_manager.sync_state_cache, args=(key,))

    @render('serial/pressure', projection='pressure/{pressure,temperature}', count=100)
    def render_pressure(self, data):
        pressure_key = self.state_manager.unique_key('pressure_pills')
        pressure_mode = st.session_state.get(pressure_key)

        if not pressure_mode or not data:
            return

        with self._pressure_plot_widget:
            data = data[self._pressure_modes[pressure_mode]]
            df = pd.DataFrame(data)
            st.line_chart(df)

    @control_stream(stream='serial')
    def gas_selection(self):
        key = 'gas_pills'
        self.state_manager.init_state(key, 'TEMPERATURE')
        with self._gas_radio_widget:
            st.pills(label="GasHt", options=["TEMPERATURE", "PRESSURE", "HUMIDITY", "GAS"], selection_mode='single',
                     label_visibility='collapsed', key=self.state_manager.unique_key(key),
                     on_change=self.state_manager.sync_state_cache, args=(key,))

    @render('serial/gas', projection='gas/{temperature,pressure,humidity,gas}', count=100)
    def render_gas_heat(self, data):
        gas_key = self.state_manager.unique_key('gas_pills')
        gas_mode = st.session_state.get(gas_key)

        if not gas_mode or not data:
            return

        with self._gas_plot_widget:
            data = data[self._gas_modes[gas_mode]]
            df = pd.DataFrame(data)
            st.line_chart(df)

    @control_stream(stream='serial')
    def imu_selection(self):
        key = 'imu_pills'
        self.state_manager.init_state(key, 'ACC')
        with self._imu_radio_widget:
            st.pills(label="Imu", options=["ACC", "GYRO", "MAG", "QUAT", "EULER", "AUX"], selection_mode='single',
                     label_visibility='collapsed', key=self.state_manager.unique_key(key),
                     on_change=self.state_manager.sync_state_cache, args=(key,))

    @render
    def display_imu(self):
        imu_key = self.state_manager.unique_key('imu_pills')
        imu_mode = st.session_state.get(imu_key)

        if not imu_mode or imu_mode not in self._imu_modes:
            return

        data = self.sensor.read(self._imu_modes[imu_mode], projection=self._imu_projections[imu_mode], count=100)
        if data:
            with self._imu_plot_widget:
                df = pd.DataFrame(data)
                st.line_chart(df)

    @render
    def display_audio(self):
        """
        Display audio data from the sensor.

        The audio data structure is a 3D structure:
        [
            {'audio': [
                numpy_array1,  # shape (n, 2)
                numpy_array2,  # shape (n, 2)
                ...
            ]},
            {'audio': ...}
        ]
        """
        # Initialize audio_history if needed - it should be a deque filled with zeros
        if not hasattr(self.sensor, 'audio_history'):
            zeros_array = np.zeros((3000, 2), dtype=np.int16)
            self.sensor.audio_history = deque(zeros_array, maxlen=3000)

        data = self.sensor.read(path='audio', count=2)
        if not data:
            return

        # Extract all valid numpy arrays from the nested structure
        audio_chunks = []
        for entry in data:
            if isinstance(entry, dict) and 'audio' in entry:
                for chunk in entry['audio']:
                    if isinstance(chunk, (list, np.ndarray)) and len(chunk) > 0:
                        # Convert to numpy array if it's a list
                        if isinstance(chunk, list):
                            try:
                                np_chunk = np.array(chunk)
                                if np_chunk.ndim == 2 and np_chunk.shape[1] == 2:
                                    audio_chunks.append(np_chunk)
                            except Exception:
                                pass
                        else:  # It's already a numpy array
                            if chunk.ndim == 2 and chunk.shape[1] == 2:
                                audio_chunks.append(chunk)

        if audio_chunks:
            try:
                # Stack all chunks into one array
                chunk = np.vstack(audio_chunks)  # shape: (n, 2)

                # downsample new chunks
                max_new_points = 80
                if len(chunk) > max_new_points:
                    step = len(chunk) // max_new_points
                    chunk = chunk[::step]

                self.sensor.audio_history.extend(chunk)
            except Exception:
                # If there's an error processing new chunks, just continue with existing history
                pass

        try:
            # Create time axis (sample index)
            buf_array = np.array(list(self.sensor.audio_history))
            df = pd.DataFrame(buf_array, columns=['Channel 1', 'Channel 2'])
            df['Sample'] = np.arange(len(df))

            # Melt for Altair multi-line plotting
            df_melted = df.melt(id_vars='Sample', var_name='Channel', value_name='Amplitude')

            # Set fixed y-axis range for visual stability
            y_max = 1250  # Max for int16 audio
            y_min = -y_max

            chart = alt.Chart(df_melted).mark_line().encode(
                x='Sample:Q',
                y=alt.Y('Amplitude:Q', scale=alt.Scale(domain=[y_min, y_max])),
                color='Channel:N'
            ).properties(
                width=700,
                height=300,
                title='Live Audio Stream'
            )

            with self._audio_widget:
                st.altair_chart(chart, use_container_width=True)
        except Exception:
            zeros_array = np.zeros((3000, 2), dtype=np.int16)
            self.sensor.audio_history = deque(zeros_array, maxlen=3000)

    @staticmethod
    def _led_values_to_string(led_array: list[tuple[int, int, int]]) -> str:
        result = ["Scheme: LED ID: (R, G, B)\nSave: Ctrl+Return"]
        for i, values in enumerate(led_array):
            result.append(f"LED {i}: ({values[0]}, {values[1]}, {values[2]})")
        return "\n".join(result)

    @staticmethod
    def _string_to_led_values(led_string) -> list[tuple[int, int, int]]:
        lines = led_string.strip().split("\n")
        led_array = []
        for line in lines[2:]:  # Skip the first two lines of the description
            parts = line.split(": ")
            if len(parts) == 2:
                rgb_values = parts[1].strip("()")  # Remove parentheses
                r, g, b = map(int, rgb_values.split(", "))
                led_array.append((r, g, b))
        return led_array

    # Overridden Methods
    def update_container(self, container: DeltaGenerator):
        """Customize the layout"""
        self._container = container.container(border=False)

        self._static_header = self._container.empty()
        self._static_area = self._container.container(border=True)

        self._dynamic_header = self._container.empty()
        self._dynamic_area = self._container.container(border=False)

        self._imu_radio_widget = self._container.empty()  # Static

        ratio = 0.7  # Width of the static area (settings)
        widgets = self._container.columns([ratio, 1 - ratio], border=False)
        self._imu_plot_widget = widgets[0].container(border=self.sensor.is_running('serial')).empty()
        self._image_widget = widgets[1].container(border=self.sensor.is_running('camera')).empty()

        ratio = 0.5
        widgets = [c.empty() for c in self._container.columns([ratio, 1 - ratio], border=False)]
        self._pressure_radio_widget, self._gas_radio_widget = widgets

        widgets = self._container.columns([ratio, 1 - ratio], border=False)
        self._pressure_plot_widget = widgets[0].container(border=self.sensor.is_running('serial')).empty()
        self._gas_plot_widget = widgets[1].container(border=self.sensor.is_running('serial')).empty()

        # Audio
        self._audio_widget = self._container.container(border=self.sensor.is_running('audio')).empty()
