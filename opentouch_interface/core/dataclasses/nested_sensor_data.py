import re


##########################################################################
# HELPER FUNCTIONS
##########################################################################

def flatten_fields(data, prefix=""):
    """
    Recursively flatten a nested dictionary.

    This function produces a dictionary mapping each full key path to its value.
    For example, given:

        data = {
            "serial": {
                "imu": {
                    "raw": {"x": 650.0, "y": -185.0}
                }
            },
            "ts": 107010
        }

    The result will include keys like:
      - "serial"
      - "serial/imu"
      - "serial/imu/raw"
      - "serial/imu/raw/x"
      - "serial/imu/raw/y"
      - "ts"

    When used with a node (for localized flattening) call with prefix="" so that keys are relative.
    """
    result = {}
    for key, value in data.items():
        full_key = key if prefix == "" else f"{prefix}/{key}"
        result[full_key] = value
        if isinstance(value, dict):
            nested = flatten_fields(value, full_key)
            result.update(nested)
    return result


def expand_projection_spec(spec: str) -> list:
    """
    Expand a projection specification that may use curly-brace shorthand.

    For example, the spec:
         "ts,raw/{x,y}"
    is expanded into:
         ["ts", "raw/x", "raw/y"]
    """
    pattern = re.compile(r'([^{,]+?)/\{([^}]+)}')
    while True:
        m = pattern.search(spec)
        if not m:
            break
        prefix = m.group(1)
        inner = m.group(2)
        fields = [f.strip() for f in inner.split(',')]
        expanded = ",".join([f"{prefix}/{field}" for field in fields])
        spec = spec[:m.start()] + expanded + spec[m.end():]
    tokens = [token.strip() for token in spec.split(',') if token.strip()]
    return tokens


##########################################################################
# CHANNEL BUFFER: RING BUFFER FOR A SINGLE CHANNEL
##########################################################################

class ChannelBuffer:
    """
    A fixed-capacity ring buffer for one channel.

    For every node (i.e. every valid path) that is inserted, an entry is stored as a tuple:
       (full_data, full_flat, local_data, local_flat)

    where:
      - full_data is the entire inserted data point.
      - full_flat is flatten_fields(full_data) with absolute keys.
      - local_data is the value at the current node (can be a dict or a primitive).
      - local_flat is:
            • flatten_fields(local_data, prefix="") if local_data is a dict, or
            • {last_key: local_data} if local_data is a primitive.

    This design enables projection lookups that first check relative keys (local_flat)
    and then absolute keys (full_flat), and even attempts to prepend the parent's path if needed.

    The buffer is implemented as a pre-allocated list with a circular index.
    """

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.entries: list = [None] * capacity
        self.index = 0
        self.size = 0

    def insert_entry(self, entry: tuple):
        """Insert an entry into the ring buffer."""
        self.entries[self.index] = entry
        self.index = (self.index + 1) % self.capacity
        if self.size < self.capacity:
            self.size += 1

    def read_full(self, count: int = None):
        """
        Return the last 'count' full data points (the full_data element of each entry).
        """
        if count is None or count > self.size:
            count = self.size
        result = []
        start = (self.index - count) % self.capacity
        for i in range(count):
            idx = (start + i) % self.capacity
            entry = self.entries[idx]
            if entry is not None:
                result.append(entry[0])
        if len(result) == 1:
            return result[0]
        return result

    def read_projection(self, fields: list, count: int = None, channel_key: str = ""):
        """
        For each projection token in 'fields', return a list of extracted values
        from the last 'count' entries.

        Lookup rules (per entry):
          1. If a token starts with the local branch name followed by "/", strip that prefix and use local_flat.
          2. If the token exactly equals the local branch name, return the entire local_data.
          3. Otherwise, attempt to find the token in full_flat (absolute lookup).
          4. If not found, try local_flat.
          5. If still not found and a parent path exists, prepend the parent's path to the token and try full_flat again.

        The channel_key is used to derive:
          - The base channel (without any grouping suffix),
          - The local branch name (the last segment), and
          - The parent path (the channel key without the last segment).
        """
        if count is None or count > self.size:
            count = self.size
        result = {field: [] for field in fields}
        start = (self.index - count) % self.capacity

        base = channel_key.split(",")[0] if channel_key else ""
        segments = base.split("/") if base else []
        local_name = segments[-1] if segments else ""
        parent = "/".join(segments[:-1]) if len(segments) > 1 else ""

        for i in range(count):
            idx = (start + i) % self.capacity
            entry = self.entries[idx]
            if entry is None:
                for field in fields:
                    result[field].append(None)
                continue

            full_flat = entry[1]
            local_flat = entry[3]
            local_data = entry[2]

            for field in fields:
                # (a) If token starts with local_name + "/", strip that prefix and use local_flat.
                if local_name and field.startswith(local_name + "/"):
                    rel_field = field[len(local_name) + 1:]
                    value = local_flat.get(rel_field)
                # (b) If token equals the local_name, return local_data.
                elif field == local_name:
                    value = local_data
                else:
                    # (c) Try absolute lookup.
                    value = full_flat.get(field)
                    if value is None:
                        # (d) Try local lookup.
                        value = local_flat.get(field)
                    if value is None and parent:
                        # (e) Prepend the parent path and try absolute lookup.
                        candidate = parent + "/" + field
                        value = full_flat.get(candidate)
                result[field].append(value)
        return result


##########################################################################
# EFFICIENT NESTED SENSOR DATA STORE
##########################################################################

class NestedSensorData:
    """
    A sensor data store that accepts only a nested dictionary on insert and
    creates a buffer for every possible path so that every valid path is addressable.

    Storage Details:
      • The insertion routine traverses the nested dictionary and registers a channel for every node.
      • The channel key is built by joining keys with "/" (e.g. "serial/imu/raw").
      • If a node is a primitive, a channel is created with its value and a one-item
        flattened dictionary.
      • If a grouping key is encountered (a key ending with "_"), its value is appended
        to the channel key (e.g. "serial/imu/raw,sensor_=3").

    For each channel, an entry is stored as:
         (full_data, full_flat, local_data, local_flat)
      where:
         - full_data is the entire inserted dictionary.
         - full_flat is a flattening of full_data with absolute key paths.
         - local_data is the value at the node.
         - local_flat is a flattening of local_data with relative keys (or a one-item dict for primitives).

    Projection Details:
      • The read() method accepts a channel key (exactly as registered) and an optional projection string.
      • If no projection is provided, it returns the full data points for that channel.
      • If a projection is provided (using, for example, curly-brace shorthand like "ts,raw/{x,y}"),
        the spec is expanded and used to extract fields from the stored entries.
      • The projection lookup first checks relative keys (local_flat), then absolute keys (full_flat),
        and finally tries to prepend the parent path if needed.

    This design favors fast access to any path (even "serial") at the expense of some memory overhead.
    """

    def __init__(self, capacity: int = 100):
        self.capacity: int = capacity
        self.channels: dict[str, ChannelBuffer] = {}  # mapping: channel_key (str) -> ChannelBuffer

    def _register_channel(self, channel_key: str):
        """Ensure a ChannelBuffer exists for the given channel key."""
        if channel_key not in self.channels:
            self.channels[channel_key] = ChannelBuffer(self.capacity)

    def _insert_recursive(self, node, full_data: dict, current_path: list, grouping: dict):
        """
        Recursively traverse the nested data and register a channel for every node.

        For each node (whether a dictionary or a primitive), the channel key is built by joining
        current_path with "/". If a grouping key (ending with '_') is encountered in the node, its
        value is recorded and appended to the channel key using comma notation.

        The stored entry for a channel is a tuple:
            (full_data, full_flat, local_data, local_flat)
        where:
            - full_flat is flatten_fields(full_data) (absolute keys),
            - local_data is the value at this node,
            - local_flat is:
                • flatten_fields(node, prefix="") if node is a dict, or
                • {last_key: node} if node is a primitive.
        """
        # Update grouping info if node is a dict.
        if isinstance(node, dict):
            local_grouping = grouping.copy()
            for key, value in node.items():
                if key.endswith('_'):
                    local_grouping[key] = str(value)
        else:
            local_grouping = grouping

        # Build the channel key for the current node.
        channel_key = "/".join(current_path) if current_path else "ROOT"
        if local_grouping:
            # For simplicity, if there is grouping info, use the first grouping key.
            group_key = next(iter(local_grouping))
            channel_key = f"{channel_key},{group_key}={local_grouping[group_key]}"
        self._register_channel(channel_key)

        # Compute flattened versions.
        full_flat = flatten_fields(full_data)
        if isinstance(node, dict):
            local_flat = flatten_fields(node, prefix="")
            local_data = node
        else:
            # For primitives, create a one-item dict keyed by the last segment.
            local_name = current_path[-1] if current_path else "ROOT"
            local_flat = {local_name: node}
            local_data = node

        entry = (full_data, full_flat, local_data, local_flat)
        self.channels[channel_key].insert_entry(entry)

        # Recurse if node is a dictionary.
        if isinstance(node, dict):
            for key, value in node.items():
                # Descend into all keys (even grouping keys, if you want every path addressable)
                self._insert_recursive(value, full_data, current_path + [key], local_grouping)

    def insert(self, data: dict):
        """
        Insert a nested dictionary into the data store.

        This method traverses the entire data structure and registers a channel for every node,
        so that every possible path (e.g. "serial", "serial/imu", "serial/imu/raw", "ts", etc.) is valid.
        """
        if not isinstance(data, dict):
            raise TypeError("Data must be a dictionary.")
        self._insert_recursive(data, data, current_path=[], grouping={})

    def read(self, channel_path: str, projection: str = None, count: int = None):
        """
        Read from the specified channel.

        Parameters:
          - channel_path: The channel key exactly as registered (e.g., "serial", "serial/imu",
                          "serial/imu/raw,sensor_=3", "ts", etc.).
          - projection: (Optional) A projection spec (which may use curly-brace shorthand, e.g., "ts,raw/{x,y}").
          - count: (Optional) The number of most-recent items to return.

        If projection is None, returns a list of full data points stored in the channel.
        Otherwise, the projection spec is expanded into tokens and used to extract fields,
        returning a dictionary mapping each token to a list of values.
        """
        cb = self.channels.get(channel_path)
        if cb is None:
            return None
        if projection is None:
            return cb.read_full(count)
        else:
            proj_tokens = expand_projection_spec(projection)
            return cb.read_projection(proj_tokens, count, channel_key=channel_path)
