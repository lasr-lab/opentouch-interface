import pprint
import queue
import time
import warnings
from collections import deque
from dataclasses import asdict
from typing import Any

import betterproto
import numpy as np
import sounddevice as sd

from opentouch_interface.core.registries.class_registries import SensorClassRegistry
from opentouch_interface.core.sensors.interfaces.digit360_interface import Digit360, PressureApData, ImuData, \
    PressureData, GasHtData
from opentouch_interface.core.sensors.touch_sensor import TouchSensor
from opentouch_interface.core.validation.sensors.digit360_config import Digit360Config


@SensorClassRegistry.register_sensor('Digit360')
class Digit360Sensor(TouchSensor):
    def __init__(self, config: Digit360Config):
        super().__init__(config=config)
        self.sensor: Digit360 | None = None

    def connect(self):
        self.sensor = Digit360(self.get('descriptor'))
        time.sleep(1)
        for idx, val in enumerate(self.get('led_values')):
            self.set('led', (idx, val))

    def set(self, attr: str, value: Any) -> Any:
        """
        Configures sensor settings like LEDs, etc.
        """
        if attr == 'led':
            # Assume 'value' looks like (channel_id, (r, g, b)) where r, g and b are values in the range [0, 255]
            idx, rgb = value
            rgb = [max(0, min(elem, 255)) for elem in rgb]

            self.sensor.led_set_channel(channel=idx, rgb=tuple(rgb))
            self._config.led_values[idx] = rgb

    def disconnect(self):
        """
        Disconnects the sensor, stopping any ongoing threads and releasing resources.
        """
        super().disconnect()
        self.sensor.disconnect()

    @TouchSensor.data_source("camera", frequency=30)
    def read_images(self):
        while True:
            yield self.sensor.get_frame()

    @TouchSensor.data_source("serial", frequency=100)  # Assuming a frequency of 100 Hz for serial data
    def read_serial(self):
        while True:
            try:
                # Read at maximum capacity
                data = self.sensor.read()
                frame_name, frame_type = betterproto.which_one_of(data, "type")

                if isinstance(frame_type, PressureApData):
                    yield {"pressure_ap": asdict(frame_type)}  # noqa (type is correct)

                if isinstance(frame_type, PressureData):
                    yield {"pressure": asdict(frame_type)}  # noqa (type is correct)

                if isinstance(frame_type, ImuData):
                    yield {"imu": asdict(frame_type)}  # noqa (type is correct)

                if isinstance(frame_type, GasHtData):
                    yield {"gas": asdict(frame_type)}  # noqa (type is correct)

            except Exception as e:
                warnings.warn(f"Error reading serial data: {e}", UserWarning)

    @TouchSensor.data_source("audio", frequency=10)
    def read_audio(self):
        """
        Generator that provides audio data from the sensor's audio input.

        Data Structure:
        The returned data has a 3D structure:
        - First dimension: A list of audio chunks (the snapshot)
        - Second dimension: Each chunk is a numpy array of shape (n, 2)
        - Third dimension: Each row in the array is a pair of [ch1, ch2] values
        """
        data_queue = queue.Queue()

        def audio_callback(indata, frames, time_info, status):
            # if status:
            #     print(f"Status: {status}")
            # Push a copy of the incoming data into the queue.
            data_queue.put(indata.copy())

        stream = sd.InputStream(
            samplerate=48000,
            channels=2,
            dtype="int16",
            callback=audio_callback,
            device=self.get('descriptor').audio
        )

        try:
            with stream:
                while self.is_running("audio"):
                    # Build a snapshot of all data currently in the queue.
                    snapshot = []

                    # Block briefly to get at least one chunk (if available).
                    try:
                        first_chunk = data_queue.get(timeout=0.1)
                        snapshot.append(first_chunk)
                    except queue.Empty:
                        # No data available; yield an empty list.
                        yield snapshot
                        continue

                    # Drain any additional items that have accumulated without blocking.
                    while True:
                        try:
                            snapshot.append(data_queue.get_nowait())
                        except queue.Empty:
                            break

                    # Yield the snapshot of accumulated data.
                    yield snapshot

        except Exception as e:
            print(f"Error during audio streaming: {e}")
            yield None

    def info(self, verbose: bool = True) -> dict:
        """
        Print and return a summary of the sensor configuration.

        If verbose is True, the configuration is pretty-printed.
        """
        config_dump = self._config.model_dump()
        del config_dump['descriptor']
        if verbose:
            pprint.pprint(config_dump)
        return config_dump

    def restart_replay(self):
        """
        Restart replay mode for all data streams.
        """
        if not self.get('replay_mode'):
            return

        super().restart_replay()

        if hasattr(self, 'audio_history') and isinstance(self.audio_history, deque):
            zeros_array = np.zeros((3000, 2), dtype=np.int16)
            self.audio_history = deque(zeros_array, maxlen=3000)
