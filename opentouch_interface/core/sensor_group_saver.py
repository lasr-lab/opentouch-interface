import os
import struct
import threading
import time
import json
from queue import Queue

import h5py
import numpy as np
import multiprocessing

from opentouch_interface.core.oti_config import OTIConfig
from opentouch_interface.core.registries.class_registries import SerializerClassRegistry
from opentouch_interface.core.serialization.base_serializer import BaseSerializer

# Type aliases for clarity.
BinaryBlob = bytes

# Maps 'sensor_name' to a dict which maps each 'data_stream' to a list of serialized elements
ChunkData = dict[str, dict[str, list[BinaryBlob]]]


def hdf5_save_data_worker(mp_queue: multiprocessing.Queue, file_path: str) -> None:
    """
    Worker function running in a separate process.
    Opens (or creates) the HDF5 file at file_path and appends each received binary chunk
    to the resizable dataset 'sensor_chunks'.

    Also maintains metadata for each chunk:
    - 'chunk_start_times': The absolute start time of each chunk (in seconds since recording started)
    - 'chunk_end_times': The absolute end time of each chunk (in seconds since recording started)
    """
    with h5py.File(file_path, "a") as hdf5_file:
        # Create the sensor_chunks dataset if it doesn't exist
        if "sensor_chunks" not in hdf5_file:
            dt = h5py.special_dtype(vlen=np.dtype("uint8"))
            dataset = hdf5_file.create_dataset("sensor_chunks", shape=(0,), maxshape=(None,), dtype=dt)
        else:
            dataset = hdf5_file["sensor_chunks"]

        # Create metadata datasets if they don't exist
        if "chunk_start_times" not in hdf5_file:
            hdf5_file.create_dataset("chunk_start_times", shape=(0,), maxshape=(None,), dtype=np.float64)

        if "chunk_end_times" not in hdf5_file:
            hdf5_file.create_dataset("chunk_end_times", shape=(0,), maxshape=(None,), dtype=np.float64)

        start_times_dataset = hdf5_file["chunk_start_times"]
        end_times_dataset = hdf5_file["chunk_end_times"]

        last_end_time = 0.0  # Track the end time of the last chunk

        while True:
            item = mp_queue.get()
            if item is None:  # Sentinel value to signal termination.
                break

            chunk_index, end_time, blob = item  # This is the end time

            # Calculate start time for this chunk
            start_time = 0.0 if chunk_index == 0 else last_end_time

            # Store the blob in the sensor_chunks dataset
            new_size = dataset.shape[0] + 1
            dataset.resize((new_size,))
            # Convert the blob (bytes) into a numpy array of uint8 and store it.
            dataset[-1] = np.frombuffer(blob, dtype=np.uint8)

            # Store the metadata
            start_times_dataset.resize((new_size,))
            start_times_dataset[-1] = start_time

            end_times_dataset.resize((new_size,))
            end_times_dataset[-1] = end_time

            # Update the last_end_time for the next chunk
            last_end_time = end_time


class SensorGroupSaver:
    """
    Handles persistence (saving) and replay of sensor data for a SensorGroup.

    Responsibilities:
      - Initialize and manage an HDF5 file for storing sensor data chunks.
      - Gather sensor data periodically, pack it into a binary blob, and send it to a separate
        process via a multiprocessing Queue for saving.
      - Provide replay functionality by reading stored chunks, unpacking them,
        deserializing each event, and enqueueing them into each sensor's replay queue.
      - Save configuration data into the HDF5 file.
    """

    def __init__(self, sensor_group) -> None:
        """
        Initialize the saver with references and control variables.

        Parameters:
          sensor_group: The parent SensorGroup instance.

          Multiprocessing-related:
          - self._mp_queue: Queue used to send packed data chunks to the saving process.
          - self._save_process: The separate process that writes data chunks to HDF5.

          Thread control for saving:
          - self._stop_event: Event used to signal the saving thread to stop.
          - self._save_thread: The thread that periodically gathers sensor data and packs it.

          Replay-related:
          - self._current_replay_chunk: Index of the next chunk to load from the HDF5 file.
          - self._replay_stop_event: Event to signal the replay refill worker to stop.
          - self._replay_thread: The thread that refills sensor replay queues during replay mode.
        """
        from opentouch_interface.core.sensor_group import SensorGroup
        self.sensor_group: SensorGroup = sensor_group

        # Multiprocessing variables.
        self._mp_queue: multiprocessing.Queue | None = None
        self._save_process: multiprocessing.Process | None = None

        # Thread control for saving.
        self._stop_event: threading.Event = threading.Event()
        self._save_thread: threading.Thread | None = None

        # Replay-related variables.
        self._current_replay_chunk: int = 0
        self._replay_stop_event: threading.Event = threading.Event()
        self._replay_thread: threading.Thread | None = None

    # @property
    # def source_path(self):
    #     return self.sensor_group.source_path

    # @property
    # def destination_path(self):
    #     return self.sensor_group.destination_path

    @property
    def abs_source(self) -> str:
        return self.sensor_group.abs_source

    @property
    def abs_destination(self) -> str:
        return self.sensor_group.abs_destination

    def _initialize_hdf5_file(self) -> None:
        """
        Ensure that the HDF5 file exists and contains a resizable dataset 'sensor_chunks'.
        This file is used to store packed binary data chunks.
        """

        # Create the parent directories
        os.makedirs(os.path.dirname(self.abs_destination), exist_ok=True)

        # Create HDF5 file
        with h5py.File(self.abs_destination, "a") as hdf5_file:
            if "sensor_chunks" not in hdf5_file:
                dt = h5py.special_dtype(vlen=np.dtype("uint8"))
                hdf5_file.create_dataset("sensor_chunks", shape=(0,), maxshape=(None,), dtype=dt)

    @staticmethod
    def pack_chunk_data(chunk_data: ChunkData) -> BinaryBlob:
        """
        Pack the sensor data chunk into a single binary blob.

        The binary format is as follows:
          - [Number of sensors] (4 bytes, unsigned int)
          For each sensor:
            - [Sensor name length] (4 bytes)
            - [Sensor name] (UTF-8 encoded bytes)
            - [Number of streams] (4 bytes)
            For each stream:
              - [Stream name length] (4 bytes)
              - [Stream name] (UTF-8 encoded bytes)
              - [Number of events] (4 bytes)
              For each event:
                - [Event length] (4 bytes)
                - [Event data] (raw binary)
        """
        blob = bytearray()
        sensors = list(chunk_data.keys())
        # Pack the number of sensors.
        blob += struct.pack("I", len(sensors))
        for sensor_name in sensors:
            sensor_bytes = sensor_name.encode("utf-8")
            # Pack sensor name length and sensor name.
            blob += struct.pack("I", len(sensor_bytes))
            blob += sensor_bytes

            sensor_buffer = chunk_data[sensor_name]  # This is a dict: stream_name -> list of events.
            streams = list(sensor_buffer.keys())
            # Pack number of streams for this sensor.
            blob += struct.pack("I", len(streams))
            for stream_name in streams:
                stream_bytes = stream_name.encode("utf-8")
                # Pack stream name length and stream name.
                blob += struct.pack("I", len(stream_bytes))
                blob += stream_bytes

                events = sensor_buffer[stream_name]  # List of binary events.
                # Pack the number of events for this stream.
                blob += struct.pack("I", len(events))
                for event in events:
                    # Pack event length and then event data.
                    blob += struct.pack("I", len(event))
                    blob += event
        return bytes(blob)

    @staticmethod
    def unpack_chunk_data(blob: BinaryBlob) -> ChunkData:
        """
        Unpack a binary blob into the original sensor data structure.
        """
        offset = 0
        chunk_data: ChunkData = {}
        # Unpack the number of sensors.
        num_sensors = struct.unpack("I", blob[offset:offset + 4])[0]
        offset += 4
        for _ in range(num_sensors):
            # Unpack sensor name length and sensor name.
            sensor_name_length = struct.unpack("I", blob[offset:offset + 4])[0]
            offset += 4
            sensor_name = blob[offset:offset + sensor_name_length].decode("utf-8")
            offset += sensor_name_length
            sensor_dict: dict[str, list[BinaryBlob]] = {}
            # Unpack number of streams for this sensor.
            num_streams = struct.unpack("I", blob[offset:offset + 4])[0]
            offset += 4
            for _ in range(num_streams):
                # Unpack stream name length and stream name.
                stream_name_length = struct.unpack("I", blob[offset:offset + 4])[0]
                offset += 4
                stream_name = blob[offset:offset + stream_name_length].decode("utf-8")
                offset += stream_name_length
                # Unpack number of events for this stream.
                num_events = struct.unpack("I", blob[offset:offset + 4])[0]
                offset += 4
                events: list[BinaryBlob] = []
                for _ in range(num_events):
                    # Unpack event length and event data.
                    event_length = struct.unpack("I", blob[offset:offset + 4])[0]
                    offset += 4
                    event_data = blob[offset:offset + event_length]
                    offset += event_length
                    events.append(event_data)
                sensor_dict[stream_name] = events
            chunk_data[sensor_name] = sensor_dict
        return chunk_data

    def _save_data_chunks(self) -> None:
        """
        Continuously gather sensor data from all sensors in the group, pack it into a binary blob,
        and send it to the saving process via the multiprocessing queue.

        This method runs in a dedicated thread.
        """
        chunk_index = 0
        while not self._stop_event.is_set():
            time.sleep(5)  # Wait for 5 seconds between data chunks.

            # For each sensor, call its read_buffer() method to get data and durations
            sensor_data = {}
            max_duration = 0.0

            for sensor in self.sensor_group.sensors:
                sensor_name = sensor.get('sensor_name')
                data, durations = sensor.read_buffer()  # Now getting durations instead of deltas
                sensor_data[sensor_name] = data

                # Find the maximum duration across all streams for this sensor
                if durations:
                    sensor_max_duration = max(durations.values(), default=0.0)
                    max_duration = max(max_duration, sensor_max_duration)

            # Pack the sensor data into a binary blob
            blob = self.pack_chunk_data(sensor_data)

            # Use the maximum duration value (time elapsed since recording started)
            if self._mp_queue is not None:
                self._mp_queue.put((chunk_index, max_duration, blob))

            chunk_index += 1

    def start_saving(self) -> None:
        """
        Initialize the HDF5 file, start the multiprocessing worker process, and launch the saving thread.
        """
        self._initialize_hdf5_file()

        # Launch the HDF5 saving process.
        self._mp_queue = multiprocessing.Queue()
        self._save_process = multiprocessing.Process(target=hdf5_save_data_worker,
                                                     args=(self._mp_queue, self.abs_destination))
        self._save_process.start()

        # Clear the stop event and start the saving thread.
        self._stop_event.clear()
        self._save_thread = threading.Thread(target=self._save_data_chunks, daemon=True)
        self._save_thread.start()

    def stop_saving(self) -> None:
        """
        Stop the saving thread and the saving process.
        """
        self._stop_event.set()
        if self._save_thread is not None:
            self._save_thread.join()
        if self._mp_queue is not None:
            self._mp_queue.put(None)  # Send sentinel value.
        if self._save_process is not None:
            self._save_process.join()
            self._save_process = None

    def start_replay(self, offset_seconds: float = 0.0) -> None:
        """
        Start replay mode by restarting each sensor's replay and launching the replay refill thread.

        Parameters:
            offset_seconds (float): Time offset (in seconds) to start replay from.
        """
        # Stop any existing replay thread before starting a new one
        self.stop_replay()

        # Instruct each sensor to restart its replay mechanism.
        for sensor in self.sensor_group.sensors:
            sensor.restart_replay()

        # Clear the stop event and reset the chunk counter
        self._replay_stop_event.clear()
        self._current_replay_chunk = 0

        # Start the replay refill worker thread with offset
        self._replay_thread = threading.Thread(
            target=self._replay_refill_worker,
            args=(offset_seconds,),
            daemon=True
        )
        self._replay_thread.start()

    def stop_replay(self) -> None:
        """
        Stop the replay refill worker thread.
        """
        self._replay_stop_event.set()
        if self._replay_thread and self._replay_thread.is_alive():
            self._replay_thread.join(timeout=2.0)
            if self._replay_thread.is_alive():
                print("Warning: Replay thread did not terminate in time.")

    def _replay_refill_worker(self, offset_seconds: float = 0.0) -> None:
        """
        Worker thread that refills sensor replay queues with events from the HDF5 file.

        This thread:
        1. Finds the appropriate starting chunk based on the offset_seconds
        2. Loads chunks sequentially and distributes events to each sensor's replay queue
        3. Filters events that occur before the requested offset
        4. Maintains a buffer of events to ensure smooth playback

        Parameters:
            offset_seconds (float): Time offset in seconds to start replay from
        """
        threshold_seconds = 4  # Buffer at least this many seconds of data
        hdf5_file = None

        try:
            # Open the HDF5 file for reading
            hdf5_file = h5py.File(self.abs_source, "r")

            # Access the datasets
            chunks_dataset = hdf5_file["sensor_chunks"]
            start_times_dataset = hdf5_file["chunk_start_times"]
            end_times_dataset = hdf5_file["chunk_end_times"]

            # Handle empty recording case
            if len(end_times_dataset) == 0:
                print("Warning: Recording contains no data")
                return

            # Handle out-of-bounds offset
            if offset_seconds > end_times_dataset[-1]:
                print(f"Warning: Offset {offset_seconds}s exceeds recording duration ({end_times_dataset[-1]}s). "
                      f"Starting from beginning.")
                offset_seconds = 0.0

            # Find the chunk containing the requested offset
            self._current_replay_chunk = 0
            for i in range(len(start_times_dataset)):
                start = start_times_dataset[i]
                end = end_times_dataset[i]

                if start <= offset_seconds < end:
                    # This chunk contains our offset time
                    self._current_replay_chunk = i
                    break

                is_not_last = i < len(start_times_dataset) - 1
                next_start = start_times_dataset[i + 1] if is_not_last else None

                if is_not_last and end <= offset_seconds < next_start:
                    # Offset is in the gap between chunks
                    self._current_replay_chunk = i + 1
                    break

            # Main loop for filling replay queues
            while not self._replay_stop_event.is_set():
                # Check if we need to refill the buffers
                need_refill = self._check_buffer_levels(threshold_seconds)

                if need_refill:
                    # Check if we've reached the end of available chunks
                    if self._current_replay_chunk >= len(chunks_dataset):
                        # No more data available
                        # print("End of replay data reached")
                        break

                    try:
                        # Load the next chunk with bounds checking
                        chunk_blob = bytes(chunks_dataset[self._current_replay_chunk])

                        # Process and distribute the chunk data
                        self._process_chunk(chunk_blob, offset_seconds)

                        # Move to the next chunk
                        self._current_replay_chunk += 1
                    except IndexError:
                        # This can happen if datasets have inconsistent lengths
                        print(f"Error: Chunk index {self._current_replay_chunk} out of range")
                        break

                # Sleep briefly before checking buffer levels again
                time.sleep(0.1)

        except Exception as e:
            print(f"Error in replay refill worker: {e}")
        finally:
            # Properly close the HDF5 file if it was opened
            if hdf5_file is not None and hdf5_file.id.valid:
                hdf5_file.close()

    def _check_buffer_levels(self, threshold_seconds: float) -> bool:
        """
        Check if any sensor's replay queues need refilling.

        Returns True if at least one queue has less than threshold_seconds of buffered data.
        """
        for sensor in self.sensor_group.sensors:
            if not sensor.replay_queues:
                return True  # Need to fill if queues aren't initialized yet

            # Check the first queue as a representative sample
            sample_queue = next(iter(sensor.replay_queues.values()))

            with sample_queue.mutex:
                events = list(sample_queue.queue)

            if not events:
                return True  # Empty queue needs filling

            # Calculate the time span of buffered events
            first_delta = events[0].get('delta', 0)
            last_delta = events[-1].get('delta', 0)
            buffered_time = last_delta - first_delta

            if buffered_time < threshold_seconds:
                return True  # Buffer too small

        return False  # All buffers are sufficiently filled

    def _process_chunk(self, chunk_blob: bytes, offset_seconds: float) -> None:
        """
        Process a chunk of data and distribute it to the appropriate sensor queues.

        Parameters:
            chunk_blob: Binary data containing the serialized events
            offset_seconds: Requested playback offset in seconds
        """
        # Unpack the binary data into a structured format
        chunk_data = self.unpack_chunk_data(chunk_blob)

        # Process each sensor's data
        for sensor in self.sensor_group.sensors:
            sensor_name = sensor.get('sensor_name')
            if sensor_name not in chunk_data:
                continue

            # Get the serializer for this sensor type
            serializer_cls = SerializerClassRegistry.get_serializer(sensor.get('sensor_type'))
            serializer = serializer_cls()

            # Process each data stream for this sensor
            for data_stream, events_list in chunk_data[sensor_name].items():
                # Initialize the replay queue if needed
                if data_stream not in sensor.replay_queues:
                    sensor.replay_queues[data_stream] = Queue()

                processed_events = []

                # Process each serialized event
                for event in events_list:
                    try:
                        # Deserialize the event
                        deserialized_event = serializer.deserialize(event)

                        # Get the absolute time of this event
                        event_time = deserialized_event.get('delta', 0)

                        # Skip events before the requested offset
                        if event_time < offset_seconds:
                            continue

                        # Keep the original delta value (Option 2)
                        processed_events.append(deserialized_event)

                    except Exception as ex:
                        print(f"Error deserializing event: {ex}")

                # Add the processed events to the queue
                if processed_events:
                    with sensor.replay_queues[data_stream].mutex:
                        sensor.replay_queues[data_stream].queue.extend(processed_events)
                        sensor.replay_queues[data_stream].not_empty.notify_all()

    @staticmethod
    def write_config(path: str, config: dict) -> bool:
        """
        Write the configuration dictionary into the HDF5 file.
        The configuration is serialized as a JSON string and stored in a dataset named "config".
        If the "config" dataset already exists, it is overwritten.

        Parameters:
          path: A absolute string path to the HDF5 file.
          config: A dictionary containing the configuration.
        """

        if not os.path.exists(path):
            return False

        json_str = json.dumps(config)
        with h5py.File(path, "a") as hdf5_file:
            if "config" in hdf5_file:
                del hdf5_file["config"]
            dt = h5py.string_dtype(encoding='utf-8')
            hdf5_file.create_dataset("config", data=json_str, dtype=dt)

        return True

    @staticmethod
    def read_config(path: str) -> dict:
        if not isinstance(path, str) or not path.strip():
            raise ValueError(f"Path must be a non-empty string, got {type(path).__name__}.")

        if not path.endswith(".touch"):
            raise ValueError("Path must point to a '.touch' file.")

        base_dir = OTIConfig.get_base_directory()
        full_path = os.path.join(base_dir, path)

        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"No such file: {full_path}")

        with h5py.File(full_path, 'r') as f:
            if 'config' not in f:
                raise KeyError(f"'config' dataset not found in the HDF5 file: {full_path}")

            raw_data = f['config'][()]
            if isinstance(raw_data, bytes):
                raw_data = raw_data.decode('utf-8')

            return json.loads(raw_data)

    @classmethod
    def get_all_decoded_data_from_file(cls, file_path: str) -> dict:
        """
        Fully de-serializes all sensor data chunks stored in the HDF5 file at file_path and returns
        a dictionary with decoded events aggregated per sensor and per stream.

        This method does not require an instance of SensorGroupSaver. It reads the configuration
        stored in the HDF5 file (via read_config) to determine sensor names and sensor types.

        The returned dictionary has the following structure:
          {
              sensor_name: {
                  stream_name: [list of decoded events],
                  ...
              },
              ...
          }

        Args:
            file_path (str): The absolute path to the HDF5 file (typically a '.touch' file).

        Returns:
            dict: A dictionary containing all decoded sensor events.
        """
        all_data: dict[str, dict[str, list]] = {}

        # Read configuration from the file to obtain sensor information.
        try:
            config = cls.read_config(file_path)
        except Exception as e:
            print(f"Error reading config from file {file_path}: {e}")
            return all_data

        # Assume the config contains a 'sensors' key with a list of sensor configurations.
        # Each sensor configuration should include 'sensor_name' and 'sensor_type'.
        sensor_info: dict[str, str] = {}
        sensors_config = config.get("sensors", [])
        for sensor in sensors_config:
            sensor_name = sensor.get("sensor_name")
            sensor_type = sensor.get("sensor_type")
            if sensor_name and sensor_type:
                sensor_info[sensor_name] = sensor_type

        try:
            with h5py.File(file_path, "r") as hdf5_file:
                if "sensor_chunks" not in hdf5_file:
                    print("No sensor_chunks dataset found in the file.")
                    return all_data

                dataset = hdf5_file["sensor_chunks"]
                # Iterate over every stored chunk.
                for i in range(dataset.shape[0]):
                    chunk_blob = bytes(dataset[i])
                    # Unpack the chunk blob into its original sensor data dictionary.
                    chunk_data: ChunkData = cls.unpack_chunk_data(chunk_blob)

                    # Process each sensor's data in the chunk.
                    for sensor_name, streams_data in chunk_data.items():
                        # Skip if sensor is not found in the config.
                        if sensor_name not in sensor_info:
                            continue

                        sensor_type = sensor_info[sensor_name]
                        try:
                            serializer_cls = SerializerClassRegistry.get_serializer(sensor_type)
                            serializer: BaseSerializer = serializer_cls()
                        except Exception as ex:
                            print(f"Could not get serializer for sensor '{sensor_name}': {ex}")
                            continue

                        # Process each stream for the sensor.
                        for stream_name, event_blobs in streams_data.items():
                            for event_blob in event_blobs:
                                try:
                                    decoded_event = serializer.deserialize(event_blob)
                                except Exception as ex:
                                    print(
                                        f"Error deserializing event for sensor '{sensor_name}', "
                                        f"stream '{stream_name}': {ex}")
                                    continue

                                if sensor_name not in all_data:
                                    all_data[sensor_name] = {}
                                if stream_name not in all_data[sensor_name]:
                                    all_data[sensor_name][stream_name] = []
                                all_data[sensor_name][stream_name].append(decoded_event)
        except Exception as e:
            print(f"An error occurred while processing the HDF5 file: {e}")

        return all_data
