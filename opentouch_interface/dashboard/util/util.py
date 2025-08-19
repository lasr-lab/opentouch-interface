import streamlit as st
from streamlit.delta_generator import DeltaGenerator


def get_clean_rendering_container() -> DeltaGenerator:
    """
    Provides a clean rendering container that alternates between two slots ('a' and 'b')
    to avoid rendering issues during state changes.

    This function swaps between two empty containers in `st.session_state` ('a' and 'b') to ensure
    that a fresh container is used for rendering on each state change, thus preventing unwanted
    re-renders or overwrites.

    :return: A Streamlit DeltaGenerator object that represents an empty container for rendering.
    :rtype: DeltaGenerator
    """
    # Retrieve the current slot in use from the session state, defaulting to 'a'
    slot_in_use = st.session_state.slot_in_use = st.session_state.get("slot_in_use", "a")

    # Toggle between slot 'a' and 'b'
    if slot_in_use == "a":
        slot_in_use = st.session_state.slot_in_use = "b"
    else:
        slot_in_use = st.session_state.slot_in_use = "a"

    # Create a dictionary mapping 'a' and 'b' to empty containers
    slot = {
        "a": st.empty(),
        "b": st.empty(),
    }[slot_in_use]

    # Return a container within the selected slot for rendering
    return slot.container()
