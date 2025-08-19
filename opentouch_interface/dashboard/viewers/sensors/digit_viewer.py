import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.core.registries.class_registries import ViewerClassRegistry
from opentouch_interface.core.sensors.touch_sensor import TouchSensor
from opentouch_interface.dashboard.viewers.base_viewer import BaseViewer, render, control_sensor


@ViewerClassRegistry.register_viewer('Digit')
class DigitViewer(BaseViewer):
    """
    Viewer class for the 'Digit' sensor, enabling visualization and control of camera data and settings.
    """

    def __init__(self, sensor: TouchSensor):
        super().__init__(sensor)
        self.image_widget = None  # Placeholder for the image widget

    # Render methods
    @render('camera', count=1)
    def display_camera(self, data):
        """Display the camera feed in the UI."""
        if not data or not len(data['camera']):
            return

        with self.image_widget:
            st.image(data['camera'], use_container_width=True)

    # Control methods
    @control_sensor(hardware_only=False)
    def settings(self):
        """Render the settings panel for the Digit sensor."""
        # Initialize state variables
        self.state_manager.init_state(
            'resolution',
            f"{self.sensor.get('resolution')} ({30 if self.sensor.get('resolution') == 'VGA' else 60} FPS)"
        )

        self.state_manager.init_state('red', self.sensor.get('rgb')[0])
        self.state_manager.init_state('green', self.sensor.get('rgb')[1])
        self.state_manager.init_state('blue', self.sensor.get('rgb')[2])

        # Create layout for settings controls
        col_res, col_red, col_green, col_blue = st.columns(4)

        # Resolution dropdown
        with col_res:
            st.selectbox(
                label='Resolution',
                options=['QVGA (60 FPS)', 'VGA (30 FPS)'],
                key=self.state_manager.unique_key('resolution'),
                on_change=self._update_resolution,
                disabled=self.is_recording,
            )

        # RGB Sliders
        with col_red:
            st.slider(
                label='Red',
                min_value=0,
                max_value=15,
                key=self.state_manager.unique_key('red'),
                on_change=self._update_rgb,
                disabled=self.is_recording,
            )

        with col_green:
            st.slider(
                label='Green',
                min_value=0,
                max_value=15,
                key=self.state_manager.unique_key('green'),
                on_change=self._update_rgb,
                disabled=self.is_recording,
            )

        with col_blue:
            st.slider(
                label='Blue',
                min_value=0,
                max_value=15,
                key=self.state_manager.unique_key('blue'),
                on_change=self._update_rgb,
                disabled=self.is_recording,
            )

    # Helper methods
    def _update_rgb(self) -> None:
        self.sensor.set('rgb', value=[
            self.state_manager.sync_state_cache('red'),
            self.state_manager.sync_state_cache('green'),
            self.state_manager.sync_state_cache('blue')
        ])

    def _update_resolution(self) -> None:
        streams = self.state_manager.sync_state_cache('resolution')
        self.sensor.set('resolution', value=streams[:-9])  # Remove FPS details

    # Overridden Methods
    def update_container(self, container: DeltaGenerator):
        """Customize the layout to display the image widget next to settings."""
        self._container = container.container(border=False)

        # Define layout proportions
        ratio = 0.8  # Width of the static area (settings)
        left, right = self._container.columns([ratio, 1 - ratio])
        self._static_header = left.empty()
        self._dynamic_header = right.empty()

        left, right = self._container.columns([ratio, 1 - ratio], border=False)
        self._static_area = left.container(border=True)
        self._dynamic_area = right.container(border=self.sensor.is_running('camera'))
        self.image_widget = self._dynamic_area.empty()
