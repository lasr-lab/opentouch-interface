import streamlit as st


class CentralRegistry:
    _sensor_group_registry = None
    _viewer_group_registry = None
    _unique_key_generator = None
    _model_registry = None

    @classmethod
    def update_container(cls, value=None):
        # Add 'update_container' to session state
        if 'update_container' not in st.session_state:
            st.session_state['update_container'] = False

        if isinstance(value, bool):
            st.session_state['update_container'] = value
        return st.session_state['update_container']

    @classmethod
    def sensor_group_registry(cls):
        from opentouch_interface.core.registries.sensor_group_registry import SensorGroupRegistry

        # Streamlit is not running. Save the state as part of the CentralRegistry
        if cls._sensor_group_registry is None:
            cls._sensor_group_registry = SensorGroupRegistry()
        return cls._sensor_group_registry

    @classmethod
    def viewer_group_registry(cls):
        from opentouch_interface.core.registries.viewer_group_registry import ViewerGroupRegistry

        # Streamlit is not running. Save the state as part of the CentralRegistry
        if cls._viewer_group_registry is None:
            cls._viewer_group_registry = ViewerGroupRegistry()
        return cls._viewer_group_registry

    @classmethod
    def unique_key_generator(cls):
        from opentouch_interface.dashboard.util.key_generator import UniqueKeyGenerator

        # Streamlit is not running. Save the state as part of the CentralRegistry
        if cls._unique_key_generator is None:
            cls._unique_key_generator = UniqueKeyGenerator()
        return cls._unique_key_generator

    @classmethod
    def model_registry(cls):
        from opentouch_interface.core.registries.model_registry import ModelRegistry

        # Streamlit is not running. Save the state as part of the CentralRegistry.
        if cls._model_registry is None:
            cls._model_registry = ModelRegistry()
        return cls._model_registry
