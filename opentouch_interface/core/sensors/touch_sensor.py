import pprint
import threading
import time
import warnings
import queue
from queue import Queue
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable

from opentouch_interface.core.dataclasses.nested_sensor_data import NestedSensorData
from opentouch_interface.core.registries.class_registries import SensorClassRegistry, SerializerClassRegistry
from opentouch_interface.core.serialization.base_serializer import BaseSerializer
from opentouch_interface.core.validation.sensor_config import SensorConfig


# Decorators
def prevent_during_recording(message: str = 'Cannot execute this method while recording is active.') -> Callable:
    """
    Skip the execution of a method if recording is active.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self._is_recording:
                warnings.warn(message, UserWarning)
                return None  # Do nothing if recording is active
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


def register_replay_fallback(target_method: str):
    """
    Register a fallback implementation for a method when in replay mode.
    """

    def decorator(func: Callable) -> Callable:
        func._fallback_for = target_method
        return func

    return decorator


def replay_mode_switch_wrapper(hardware_method: Callable, fallback_method: Callable, method_name: str) -> Callable:
    """
    Wrap a method to switch its behavior based on replay mode.

    In replay mode, the fallback method (if provided) is used;
    otherwise, the base class default is called.
    In hardware mode, the original method is executed.
    """

    @wraps(hardware_method)
    def wrapper(self, *args, **kwargs):
        if self._config.replay_mode:
            if fallback_method is not None:
                return fallback_method(self, *args, **kwargs)
            else:
                base_method = getattr(TouchSensor, method_name, None)
                if base_method is not None:
                    return base_method(self, *args, **kwargs)
                else:
                    print(f"[Replay mode] No fallback for '{method_name}'; doing nothing.")
                    return None
        else:
            return hardware_method(self, *args, **kwargs)

    return wrapper


class TouchSensor(ABC):
    """
    Base class defining the interface and shared functionality for touch sensors.

    _data_sources is a class-level registry mapping sensor class names to their
    data stream configurations. Each configuration contains a data generator
    and a frequency.
    """

    _data_sources: dict[str, dict[str, dict[str, Callable | float]]] = {}  # SensorClass -> Data stream mappings

    # -------------------------------------------------------------------------
    # Subclass Hook for Dynamic Behavior
    # -------------------------------------------------------------------------
    def __init_subclass__(cls, **kwargs):
        """
        Customize subclass behavior by wrapping methods.

        This hook automatically wraps certain methods to adjust behavior during
        replay mode and to prevent execution while recording is active.
        """
        super().__init_subclass__(**kwargs)
        cls._wrap_replay_methods()
        cls._wrap_prevent_recording_methods()
        cls._wrap_init_for_auto_connection_and_data_stream_start()

    @classmethod
    def _wrap_replay_methods(cls):
        """
        Wrap methods that require alternate behavior in replay mode.

        Methods like 'connect', 'set', and 'disconnect' are wrapped to call a
        fallback implementation if available when in replay mode.
        """
        methods_with_replay_override = ['connect', 'set', 'disconnect']

        replay_fallbacks = {
            attr_value._fallback_for: attr_value  # noqa SLF001
            for attr_name, attr_value in cls.__dict__.items()
            if callable(attr_value) and hasattr(attr_value, '_fallback_for')
        }

        for method_name in methods_with_replay_override:
            method = getattr(cls, method_name, None)
            if method:
                wrapped_method = replay_mode_switch_wrapper(
                    method, replay_fallbacks.get(method_name), method_name
                )
                setattr(cls, method_name, wrapped_method)

    @classmethod
    def _wrap_prevent_recording_methods(cls):
        """
        Wrap methods that should not execute while recording is active.

        Methods like 'set', 'disconnect', 'start_data_stream', and 'stop_data_stream'
        will issue a warning and skip execution if recording is in progress.
        """
        methods_to_prevent = ['set', 'disconnect', 'start_data_stream', 'stop_data_stream']
        for method_name in methods_to_prevent:
            method = getattr(cls, method_name, None)
            if method and callable(method):
                wrapped_method = prevent_during_recording(
                    f"Method 'TouchSensor.{method_name}' cannot be executed while recording. Returning None."
                )(method)
                setattr(cls, method_name, wrapped_method)

    @classmethod
    def _wrap_init_for_auto_connection_and_data_stream_start(cls):
        """
        Wrap the __init__ method to automatically connect to hardware and start data streams.

        When an instance is created, this ensures that in hardware mode the sensor
        connects automatically and that any data streams configured in the data_streams
        list are started.
        """
        original_init = cls.__init__

        @wraps(original_init)
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            if not self._config.replay_mode:
                self.connect()
            cls_name = self.__class__.__name__
            for data_stream in TouchSensor._data_sources.get(cls_name, {}):
                if data_stream in self.get('data_streams'):
                    self.start_data_stream(data_stream)

        cls.__init__ = new_init

    # -------------------------------------------------------------------------
    # Initialization and Configuration
    # -------------------------------------------------------------------------
    def __init__(self, config: SensorConfig):
        """
        Initialize the touch sensor with the provided configuration.

        Instance attributes are set up for tracking sensor state, active threads,
        recording data, and replay data.
        """
        # Map data stream names to their worker threads.
        self._threads: dict[str, threading.Thread] = {}
        # Track whether each data stream is currently running.
        self._running: dict[str, bool] = {}
        # Store the most recent sensor values.
        self._recent_values: NestedSensorData = NestedSensorData()
        # Double buffer for recorded data.
        self._recorded_buffers: list[dict[str, list]] = [{}, {}]
        # Store latest timestamp (seconds since recording started) per stream in each buffer
        self._stream_durations: list[dict[str, float]] = [{}, {}]
        self._active_buffer_index: int = 0  # Which buffer is currently active for writing.
        # Lock for thread-safe buffer swapping and writing.
        self._buffer_lock = threading.Lock()
        # Flag indicating whether recording is active.
        self._is_recording: bool = False
        # Time when recording started.
        self._recording_start_time: float = 0
        # Sensor configuration object.
        self._config: SensorConfig = config
        # For replay mode: a thread-safe queue for each data stream.
        self.replay_queues: dict[str, Queue] = {}

    # -------------------------------------------------------------------------
    # Connection Methods
    # -------------------------------------------------------------------------
    @abstractmethod
    def connect(self):
        """
        Establish a connection to the hardware sensor.

        In replay mode, calling this method issues a warning.
        """
        if self._config.replay_mode:
            warnings.warn('You may not call TouchSensor.connect() while in replay mode.')

    def disconnect(self) -> None:
        """
        Disconnect the sensor by stopping all data streams and recording.

        This method stops any active recording and stops all data stream threads.
        """
        self.stop_recording()
        for data_stream in list(self._running):
            self.stop_data_stream(data_stream)

    # -------------------------------------------------------------------------
    # Configuration Access Methods
    # -------------------------------------------------------------------------
    def set(self, attr: str, value: Any) -> Any:
        """
        Set a sensor attribute.

        In replay mode, this operation is not allowed and will issue a warning.
        """
        if self._config.replay_mode:
            warnings.warn('You may not call TouchSensor.set() while in replay mode.')
            return None
        warnings.warn(f"Attribute '{attr}' not supported by '{self.get('sensor_type')}'.")

    def get(self, attr: str, as_dict: bool = False) -> Any:
        """
        Retrieve a sensor attribute from the configuration.

        This method checks for the attribute on the configuration object or from a
        dumped version if as_dict is True.
        """
        if as_dict:
            return self._config.model_dump().get(attr, None)
        if hasattr(self._config, attr):
            return getattr(self._config, attr)
        return None

    def info(self, verbose: bool = True) -> dict:
        """
        Print and return a summary of the sensor configuration.

        If verbose is True, the configuration is pretty-printed.
        """
        config_dump = self._config.model_dump()
        if verbose:
            pprint.pprint(config_dump)
        return config_dump

    # -------------------------------------------------------------------------
    # Data Reading Methods
    # -------------------------------------------------------------------------
    def read(self, path: str, projection: str = None, count: int = None) -> Any:
        """
        Read sensor data for a given data stream.

        The first segment of the provided path is used to determine the data stream.
        """
        return self._recent_values.read(path, projection, count)

    # -------------------------------------------------------------------------
    # Data Stream Control Methods
    # -------------------------------------------------------------------------
    def is_running(self, path: str) -> bool:
        """
        Check if a data stream is currently active.

        The data stream is identified by the first segment of the path.
        """
        data_stream = path.split('/')[0]
        return self._running.get(data_stream, False)

    def any_running(self) -> bool:
        return any(self._running.values())

    def start_data_stream(self, data_stream: str) -> None:
        """
        Begin data collection for the specified data stream.

        If the data stream is registered and not already running, a worker thread is started
        to either fetch data from hardware or replay recorded events.
        """
        cls_name = self.__class__.__name__
        if data_stream not in TouchSensor._data_sources.get(cls_name, {}):
            warnings.warn(f"Data stream '{data_stream}' is not registered for class '{cls_name}'.", UserWarning)
            return

        if self.is_running(data_stream):
            print(f"Data stream '{data_stream}' is already running.")
            return

        # Mark the data stream as running and add it to the active data streams.
        self._running[data_stream] = True
        if data_stream not in self._config.data_streams:
            self._config.data_streams.append(data_stream)

        def data_stream_worker():
            """
            Worker function for a data stream.
            In replay mode, it consumes events from a replay queue;
            in hardware mode, it continuously fetches data from the registered generator.
            """

            serializer_cls = SerializerClassRegistry.get_serializer(self.get('sensor_type'))
            if not serializer_cls:
                raise ValueError(f'Serializer class for {self.get("sensor_type")} not found.')
            serializer: BaseSerializer = serializer_cls()

            def process_data(data_, delta_):
                self._recent_values.insert({data_stream: data_})
                if self._is_recording and delta_:
                    binary_data = serializer.serialize(data_stream, data_, delta_)
                    with self._buffer_lock:
                        self._recorded_buffers[self._active_buffer_index].setdefault(data_stream, []).append(
                            binary_data)
                        # Store the most recent delta value per data stream (duration since recording started)
                        self._stream_durations[self._active_buffer_index][data_stream] = delta_
            try:
                if self.get('replay_mode'):
                    # Ensure a replay queue exists for this data stream.
                    self.replay_queues.setdefault(data_stream, Queue())
                    previous_delta = None
                    while self.is_running(data_stream):
                        try:
                            # Expecting a dict with keys mapping to (delta, data)
                            event = self.replay_queues[data_stream].get(timeout=1)
                        except queue.Empty:
                            continue  # No event available; try again

                        delta, data = event.values()
                        process_data(data, delta)

                        # If this is the first event, don't sleep
                        if previous_delta is None:
                            sleep_duration = 0.001
                        else:
                            sleep_duration = max(delta - previous_delta, 0.001)

                        time.sleep(sleep_duration)
                        previous_delta = delta
                else:
                    # --- Hardware Mode ---
                    data_gen = TouchSensor._data_sources[cls_name][data_stream]["generator"]
                    frequency = TouchSensor._data_sources[cls_name][data_stream]["frequency"]
                    interval = 1.0 / frequency

                    for data in data_gen(self):
                        if not self.is_running(data_stream):
                            break

                        # Start time
                        loop_start = time.monotonic()

                        # Time stamps
                        delta = time.time() - self._recording_start_time
                        process_data(data, delta)

                        # Determine how much time was spent in processing.
                        elapsed = time.monotonic() - loop_start
                        sleep_duration = max(interval - elapsed, 0)
                        time.sleep(sleep_duration)
            finally:
                # Mark the data stream as no longer running after the worker finishes.
                self._running[data_stream] = False

        thread = threading.Thread(target=data_stream_worker, daemon=True)
        self._threads[data_stream] = thread
        thread.start()

    def stop_data_stream(self, data_stream: str) -> None:
        """
        Stop data collection for the specified data stream.

        This signals the worker thread to stop and waits for its termination.
        """
        if self.is_running(data_stream):
            self._running[data_stream] = False
            if data_stream in self._config.data_streams:
                self._config.data_streams.remove(data_stream)

        if data_stream in self._threads:
            self._threads[data_stream].join()

    # -------------------------------------------------------------------------
    # Recording Control Methods
    # -------------------------------------------------------------------------
    def start_recording(self) -> None:
        """
        Begin recording data for all active data streams.
        Initializes the active buffer and sets the recording flag.
        """
        if not self._is_recording:
            with self._buffer_lock:
                # Clear the active buffer before starting recording.
                self._recorded_buffers[self._active_buffer_index] = {}
            self._recording_start_time = time.time()
            self._is_recording = True

    def stop_recording(self):
        """
        Stop recording data and return the collected recordings.

        This method resets the recording flag and clears the recording buffers.
        """
        if self._is_recording:
            self._is_recording = False

    # -------------------------------------------------------------------------
    # Replay and Data Source Methods
    # -------------------------------------------------------------------------
    def restart_replay(self):
        """
        Restart replay mode for all data streams.
        """
        if not self.get('replay_mode'):
            return

        # Clear replay queues
        self._recent_values = NestedSensorData()
        for q in self.replay_queues.values():
            with q.mutex:
                q.queue.clear()

    def read_buffer(self) -> tuple[dict[str, list], dict[str, float]]:
        old_index = self._active_buffer_index
        with self._buffer_lock:
            self._active_buffer_index = 1 - old_index
            data_to_return = self._recorded_buffers[old_index]
            durations_to_return = self._stream_durations[old_index]
        # Reset the durations and buffers for this index
        self._stream_durations[old_index] = {}
        self._recorded_buffers[old_index] = {}
        return data_to_return, durations_to_return

    @staticmethod
    def data_source(data_stream: str, frequency: float) -> Callable:
        """
        Decorator to register a data generator for a specific data stream.

        The decorated function is stored in a class-wide registry along with its frequency.
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                return func(self, *args, **kwargs)

            cls_name = func.__qualname__.split('.')[0]
            if cls_name not in TouchSensor._data_sources:
                TouchSensor._data_sources[cls_name] = {}

            TouchSensor._data_sources[cls_name][data_stream] = {
                "generator": func,
                "frequency": frequency
            }
            return wrapper

        return decorator

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    @property
    def is_recording(self) -> bool:
        """
        Check if the sensor is currently recording data.
        """
        return self._is_recording

    @classmethod
    def get_data_streams(cls, sensor_type: str):
        """
        Retrieve the available data streams for a given sensor type.

        This method uses the SensorClassRegistry to determine the sensor class name
        and then returns the registered data stream names.
        """
        sensor_cls = SensorClassRegistry.get_sensor(sensor_type)
        return TouchSensor._data_sources.get(sensor_cls.__name__, {}).keys()
