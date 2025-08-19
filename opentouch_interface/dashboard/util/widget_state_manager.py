import streamlit as st

from opentouch_interface.core.registries.central_registry import CentralRegistry
from opentouch_interface.dashboard.util.key_generator import UniqueKeyGenerator


class WidgetStateManager:
    def __init__(self):
        # State management for unique keys and cached state values
        self._keys = {}
        self._state_cache = {}

    def unique_key(self, identifier: str) -> str:
        """
        Generate or retrieve a unique key for a given identifier.
        """
        # Check if the key already exists, otherwise generate a new one
        if identifier not in self._keys:
            key_generator: UniqueKeyGenerator = CentralRegistry.unique_key_generator()
            self._keys[identifier] = f"{identifier}_{key_generator.get_key()}"
        return self._keys[identifier]

    def init_state(self, identifier: str, default_value):
        """
        Initialize a Streamlit session state variable.
        """
        key = self.unique_key(identifier)

        # print(f'Key for {identifier}: {key}')

        if self._state_cache.get(key) is None:
            # Cache the default value for the key
            self._state_cache[key] = default_value
            # print(f'\'{identifier}\' was None. Setting to {default_value}')

        if key not in st.session_state:
            # Set the session state value if it does not exist
            st.session_state[key] = self._state_cache[key]
            # print(f'Setting session state value of \'{identifier}\' to {st.session_state[key]}')

        return st.session_state[key]

    def sync_state_cache(self, identifier: str):
        """
        Sync the session state variable with the internal state cache.
        """
        key = self.unique_key(identifier)

        # Update the cache with the current session state value
        self._state_cache[key] = st.session_state[key]
        # print(f'Session state of \'{identifier}\' was/is {st.session_state[key]}')
        # print(f'Setting state value of \'{identifier}\' to {self._state_cache[key]}')
        return self._state_cache[key]

    def get_state(self, identifier: str):
        return self._state_cache.get(self.unique_key(identifier))

    def set_state(self, identifier: str, value):
        key = self.unique_key(identifier)

        st.session_state[key] = value
        self._state_cache[key] = value

    def remove_from_state_cache(self, identifier: str):
        key = self.unique_key(identifier)
        if key in self._state_cache:
            del self._state_cache[key]
            del self._keys[identifier]
