import streamlit as st
from streamlit.delta_generator import DeltaGenerator


def get_clean_rendering_container() -> DeltaGenerator:
    """
    Ensure a clean rendering container on state changes.
    """
    slot_in_use = st.session_state.slot_in_use = st.session_state.get("slot_in_use", "a")
    if slot_in_use == "a":
        slot_in_use = st.session_state.slot_in_use = "b"
    else:
        slot_in_use = st.session_state.slot_in_use = "a"

    slot = {
        "a": st.empty(),
        "b": st.empty(),
    }[slot_in_use]

    return slot.container()


class UniqueKeyGenerator:
    """ Class to generate unique keys """

    def __init__(self):
        self._index = 0

    def get_key(self) -> int:
        """ Generate unique key """
        key = self._index
        self._index += 1
        return key
