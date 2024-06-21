from time import sleep
from streamlit.runtime.state import get_session_state
import streamlit as st

init_key = "__init_values__"


def main():
    view = st.radio("View", ["view1", "view2"])

    if view == "view1":
        text_input("Text1", key="text1")
        "☝️ Enter some text, then click on view2 above"
    elif view == "view2":
        "☝️ Now go back to view1 and see if your text is still there"

    st.write(st.session_state)


def text_input(label, key):
    if init_key not in st.session_state:
        st.session_state[init_key] = {}
    initial_values = st.session_state[init_key]
    try:
        value = initial_values[key]
    except KeyError:
        value = st.session_state.get(key, "")
        initial_values[key] = value

    value = st.text_input(label, value=value)

    st.session_state[key] = value
    return value


def ensure_hidden_widgets_loaded():
    new_session_state = get_session_state()._state._new_session_state
    for key, value in st.session_state.items():
        if key in new_session_state or key == init_key:
            continue
        st.session_state[init_key][key] = value


try:
    main()
finally:
    ensure_hidden_widgets_loaded()
