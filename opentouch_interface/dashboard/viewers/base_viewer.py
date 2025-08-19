import functools
import inspect

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.core.sensors.touch_sensor import TouchSensor
from opentouch_interface.dashboard.util.widget_state_manager import WidgetStateManager


def render(*args, **kwargs):
    """
    Decorator to register a method for rendering dynamic sensor data.

    Supports two usages:

    1. Without arguments:
         @render
       - The decorated method is called without any parameters.
       - Attributes set:
            _is_registered: True.
            _render_no_args: True.

    2. With arguments:
         @render(modality, projection, count)
         or using keyword arguments:
         @render(modality=<value>, projection=<value>, count=<value>)
       - The decorated method is called with sensor data.
       - Behavior:
            * Before executing the function, the wrapper checks if the sensor modality is running
              (using self.sensor.is_running(modality)). If not, it returns None.
            * If running, it reads sensor data using the provided parameters and passes the data
              to the decorated function.
       - Attributes set:
            _is_registered: True.
            _render_no_args: False.
            modality: Specifies the sensor modality.
            projection: Specifies a projection/filter on the sensor data.
            count: Specifies the number of sensor data items to read.
    """
    # Usage: @render (no arguments)
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]
        func._is_registered = True
        func._render_no_args = True

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        wrapper._is_registered = True
        wrapper._render_no_args = True
        return wrapper
    else:
        # Usage: @render(modality, projection, count) or with keyword arguments.
        modality = args[0] if args else kwargs.get('modality')
        projection = args[1] if len(args) > 1 else kwargs.get('projection')
        count = args[2] if len(args) > 2 else kwargs.get('count')

        def decorator(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                if not self.sensor.is_running(modality):
                    return None
                data = self.sensor.read(modality, projection, count)
                return func(self, data)

            wrapper._is_registered = True
            wrapper._render_no_args = False
            wrapper.modality = modality
            wrapper.projection = projection
            wrapper.count = count
            return wrapper

        return decorator


def control_sensor(hardware_only=False):
    """
    Decorator to mark a method for rendering static sensor settings.

    This decorator is used for methods that render sensor settings that are not associated
    with a specific data stream.

    Parameters:
      hardware_only (bool): If True and replay mode is active, the method is skipped.
                            Otherwise, in replay mode, interactive widgets are disabled.

    Behavior:
      - In normal mode, the method is called normally.
      - In replay mode:
            * If hardware_only is True, the method returns None.
            * Otherwise, the method is wrapped using disable_all_widgets so that
              interactive widgets are rendered in a disabled state.

    Attributes attached:
      - _is_sensor_settings: True.
      - _hardware_only: Set to the provided hardware_only value.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # If hardware_only is True and replay_mode is active, skip rendering this function.
            if hardware_only and self.sensor.get('replay_mode'):
                return None
            # In replay mode, disable widgets.
            if self.sensor.get('replay_mode'):
                return disable_all_widgets(func)(self, *args, **kwargs)
            return func(self, *args, **kwargs)

        wrapper._is_sensor_settings = True
        wrapper._hardware_only = hardware_only
        return wrapper

    return decorator


def control_stream(stream):
    """
    Decorator to mark a method for rendering static stream settings.

    This decorator is used for methods that render settings associated with a specific
    data stream. It requires a stream identifier.

    Parameters:
      stream: An identifier for the data stream. The decorated method will be called
              only if the sensor indicates that this stream is running.

    Behavior:
      - Before calling the decorated method, the decorator checks whether the stream is running
        (via self.sensor.is_running(stream)).
      - If the stream is not running, the decorated method returns None and is not executed.
      - Otherwise, the method is called normally.

    Attributes attached:
      - _is_stream_settings: True.
      - _stream: Set to the provided stream identifier.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.sensor.is_running(stream):
                return None
            return func(self, *args, **kwargs)

        wrapper._is_stream_settings = True
        wrapper._stream = stream
        return wrapper

    return decorator


def disable_all_widgets(func):
    """
    A decorator that temporarily monkey-patches all interactive widget functions
    that support the 'disabled' parameter so that they are rendered in a disabled state.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Save original widget functions in a dictionary.
        original_functions = {
            'button': st.button,
            'download_button': st.download_button,
            'checkbox': st.checkbox,
            'radio': st.radio,
            'selectbox': st.selectbox,
            'multiselect': st.multiselect,
            'slider': st.slider,
            'select_slider': st.select_slider,
            'text_input': st.text_input,
            'text_area': st.text_area,
            'number_input': st.number_input,
            'date_input': st.date_input,
            'time_input': st.time_input,
            'file_uploader': st.file_uploader,
            'color_picker': st.color_picker,
            'pills': st.pills,
        }

        # A factory function that returns a wrapped version of the widget function.
        def make_disabled(func):
            def disabled_func(*args, **kwargs):
                kwargs['disabled'] = True  # Force the widget to be disabled.
                return func(*args, **kwargs)

            return disabled_func

        # Replace each widget function with its disabled version.
        st.button = make_disabled(original_functions['button'])
        st.download_button = make_disabled(original_functions['download_button'])
        st.checkbox = make_disabled(original_functions['checkbox'])
        st.radio = make_disabled(original_functions['radio'])
        st.selectbox = make_disabled(original_functions['selectbox'])
        st.multiselect = make_disabled(original_functions['multiselect'])
        st.slider = make_disabled(original_functions['slider'])
        st.select_slider = make_disabled(original_functions['select_slider'])
        st.text_input = make_disabled(original_functions['text_input'])
        st.text_area = make_disabled(original_functions['text_area'])
        st.number_input = make_disabled(original_functions['number_input'])
        st.date_input = make_disabled(original_functions['date_input'])
        st.time_input = make_disabled(original_functions['time_input'])
        st.file_uploader = make_disabled(original_functions['file_uploader'])
        st.color_picker = make_disabled(original_functions['color_picker'])
        st.pills = make_disabled(original_functions['pills'])

        try:
            # Execute the decorated function; within this scope, all widgets are disabled.
            return func(*args, **kwargs)
        finally:
            # Restore all original widget functions.
            st.button = original_functions['button']
            st.download_button = original_functions['download_button']
            st.checkbox = original_functions['checkbox']
            st.radio = original_functions['radio']
            st.selectbox = original_functions['selectbox']
            st.multiselect = original_functions['multiselect']
            st.slider = original_functions['slider']
            st.select_slider = original_functions['select_slider']
            st.text_input = original_functions['text_input']
            st.text_area = original_functions['text_area']
            st.number_input = original_functions['number_input']
            st.date_input = original_functions['date_input']
            st.time_input = original_functions['time_input']
            st.file_uploader = original_functions['file_uploader']
            st.color_picker = original_functions['color_picker']
            st.pills = original_functions['pills']

    return wrapper


class BaseViewer:
    """
    Base class for creating sensor viewers with dynamic data and static settings rendering.

    Dynamic rendering:
      - Methods decorated with @render are discovered and registered.
      - If the method was decorated without arguments, it is called without parameters.
      - Otherwise, sensor data is fetched (if the sensor modality is running) and passed to the method.

    Static settings rendering:
      - Sensor settings (decorated with @control_sensor) are rendered unless in replay mode and marked as hardware_only.
      - Stream settings (decorated with @control_stream) are rendered only if the corresponding stream is running.
      - The decorators themselves perform the necessary checks, so the rendering loop remains simple.
    """

    def __init__(self, sensor: TouchSensor):
        # Containers for organizing content
        self._container = None  # The surrounding container for a viewer
        self._static_header = None  # Placeholder for 'Settings' header
        self._static_area = None  # Container for static content (settings)
        self._dynamic_header = None  # Placeholder for 'Live View' header
        self._dynamic_area = None  # Container for dynamic data (video streams, plots, ...)

        # Lists to store methods decorated with @render and @control
        self._data_handlers = []  # List of methods marked with @render
        self._setting_handlers = []  # List of methods marked with @control
        self._init_handlers()  # Discover and register handlers

        # Sensor instance for accessing data
        self.sensor: TouchSensor = sensor

        # Keeps the value of a widget even after switching pages
        self.state_manager = WidgetStateManager()

    # Public methods
    def update_container(self, container: DeltaGenerator):
        """
        Initialize the main container and create placeholders for static and dynamic sections.
        """
        self._container = container.container(border=False)
        self._static_header = self._container.empty()
        self._static_area = self._container.container(border=True)
        self._dynamic_header = self._container.empty()
        self._dynamic_area = self._container.container(border=False)

        # Dynamically create additional containers for widget attributes ending with '_widget'
        for attr_name in dir(self):
            if attr_name.endswith('_widget'):
                setattr(self, attr_name, self._container.container(border=True).empty())

    def render_dynamic_content(self):
        """
        Render dynamic (real-time) content based on sensor data.

        For each registered dynamic handler:
          - If the method was decorated without arguments, it is called directly.
          - If the method requires sensor data, its wrapper first checks whether the sensor modality is running.
            If not, the method returns None. Otherwise, sensor data is read and passed to the function.
        """
        if not self.sensor.any_running():
            return

        self._dynamic_header.markdown(f'###### Live Data ({self.sensor.get("sensor_name")})')
        with self._dynamic_area:
            for func in self._data_handlers:
                func()

    def render_static_content(self):
        """
        Render static settings content.

        Both sensor settings (decorated with @control_sensor) and stream settings (decorated with @control_stream)
        are rendered. The decorators themselves handle:
          - Skipping sensor settings in replay mode when hardware_only is True.
          - Rendering stream settings only if the corresponding stream is running.
        """
        if not self._setting_handlers:
            return

        # Show the header iff
        # - control_sensor has any registered methods (AND)
        # - if we are in replay mode, there should be at least one option who's _hardware_only is False

        has_control_sensor = any(getattr(f, '_is_sensor_settings', False) for f in self._setting_handlers)
        replay_mode = self.sensor.get('replay_mode')
        has_replay_settings = any(
            hasattr(f, '_hardware_only') and not getattr(f, '_hardware_only') for f in self._setting_handlers)

        if has_control_sensor and (not replay_mode or has_replay_settings):
            self._static_header.markdown(f'###### Settings ({self.sensor.get("sensor_name")})')

        with self._static_area:
            for func in self._setting_handlers:
                func()

    @property
    def is_recording(self):
        return self.sensor.is_recording

    # Private methods
    def _init_handlers(self):
        """
        Discover and register class methods decorated with @render, @control_sensor, or @control_stream.

        - Methods with _is_registered are added to _data_handlers.
        - Methods with _is_sensor_settings or _is_stream_settings are added to _setting_handlers.
        """
        for name, method in inspect.getmembers(self.__class__, predicate=inspect.isfunction):
            if getattr(method, "_is_registered", False):
                # Register methods marked with @render for dynamic content
                bound_method = method.__get__(self, self.__class__)
                self._data_handlers.append(bound_method)
            if getattr(method, "_is_sensor_settings", False) or getattr(method, "_is_stream_settings", False):
                # Register methods marked with @control_sensor or @control_stream
                bound_method = method.__get__(self, self.__class__)
                self._setting_handlers.append(bound_method)
