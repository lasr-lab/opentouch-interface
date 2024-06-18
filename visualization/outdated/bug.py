import time
from typing import Final

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

STREAMLIT_LOGO: Final = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAASCAYAAAA6yNxSAAACaEl"
    "EQVRIS62VMW/TQBTH7yVhASmUmQH3E+AiBoQQpCCkNh2AbxA+QTIyIMUoFXOzsVE+QZmqDqWY"
    "qo2QEilOBVK3euiCEMgZnMTJ+R7vnLh1kqudprzFlnzvvZ//7393wK4QX3JPC5SuPTP3jHnLw"
    "LyJX3M5XbB0U+YLBsvPzV1znlpzA9DfW4zB3WFTtFNMLC2bpnNZCMC1NYshNpkQ72Bnx56lAD"
    "UnyaE8vharNIrSLPmG/kDzr6XKiOwVYD5vMBgVQ9xMAolKP9ksaRSGri/4mRtlBiwARYZVwJU"
    "VjaXTJ5FiDimywTqdKigkHZd+EkE9CtmYZ64XgUGJmi+EWemBvxh4gFT4TCq8mCg3BaKWfgpi"
    "bBRv7z80qHEx2nhoG/xWadRyQ4DV1Zcsldq6YH7SWCXTdVuh65PmLEex73Y0Wkc+AflUBL6u1"
    "GubZ7uAVLBJhTsXFe/6/umRx20X8VESAKI4PXC9rA+QVbZGbGd4RzMsy4kCbBBAMam4BGn0+n"
    "8GZ1tQneH4fN/q8cdKAMY+rdcPC/LbOcC0GWNZfnNhHXsexIEcdfutv0KMzorzcj7Dpff1Gp0"
    "jEYDAC/m8SSo8SVIh+j0O5IJRtCr1Qz2sMXYSEkCBAD5eBiBce+L1D2zuLyKD29H86VEMzacE"
    "GKngEMTNeSBkjgokOor0wL0lzRcHMJMZkwB/9DzzF8d7ACwbjoIDbIXmiwPQSYHglrtqcCHax"
    "/1BU4K0BbeaXa+83vhuRusqb0Pywn9RIWwkQX56gw/63u6byZ+KvY6DeyKT0YIkIeRz+J4cNp"
    "2s9ijPge3tYMup4h8/q0x/QO4oIAAAAABJRU5ErkJggg=="
)

LOREM_IPSUM: Final = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod"
    " tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim"
    " veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea"
    " commodo consequat. Duis aute irure dolor in reprehenderit in voluptate"
    " velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint"
    " occaecat cupidatat non proident, sunt in culpa qui officia deserunt"
    " mollit anim id est laborum."
)


def logo_state(dg: DeltaGenerator) -> None:
    for _ in range(5):
        # Pretend we're doing an expensive operation in order to increase
        # lingering time of old UI elements. Highlights the problem in a better way.
        time.sleep(0.3)
        cols = dg.container().columns(spec=(1, 1, 1, 1, 1))

        # Display streamlit logos
        for col in cols:
            col.image(STREAMLIT_LOGO, width=100)


def text_state(dg: DeltaGenerator) -> None:
    for _ in range(5):
        # Pretend we're doing an expensive operation in order to increase
        # lingering time of old UI elements. Highlights the problem in a better way.
        time.sleep(0.3)

        dg.markdown(LOREM_IPSUM)


def button_state(dg: DeltaGenerator) -> None:
    # Pretend we're doing an expensive operation in order to increase
    # lingering time of old UI elements. Highlights the problem in a better way.
    with dg:
        with st.spinner("Doing hard work..."):
            time.sleep(3)

    dg.button("Foo")
    dg.button("Bar")
    dg.button("Baz")
    dg.button("Foobar")


def get_clean_rendering_container(app_state: str) -> DeltaGenerator:
    """Makes sure we can render from a clean slate on state changes."""
    # If app_state != previous_state, "swap" slot_in_use
    slot_in_use = st.session_state.slot_in_use = st.session_state.get("slot_in_use", "a")
    if app_state != st.session_state.get("previous_state", app_state):
        if slot_in_use == "a":
            slot_in_use = st.session_state.slot_in_use = "b"
        else:
            slot_in_use = st.session_state.slot_in_use = "a"

    st.session_state.previous_state = app_state

    slot = {
        "a": st.empty(),
        "b": st.empty(),
    }[slot_in_use]

    return slot.container()


def main() -> None:
    st.set_page_config(
        page_title="Clean-slate Rendering",
        page_icon="🔁",
        initial_sidebar_state="expanded",
    )

    st.sidebar.header("Clean-slate Rendering Demo")
    st.sidebar.caption("As requested in https://github.com/streamlit/streamlit/issues/6063")
    st.sidebar.write(
        "This is a demo that showcases two different ways of re-rendering an app in the case where"
        " a **state change** has occurred. By **state change** we mean that the app was triggered"
        " to render in a fundamentally different way than it had been. We're trying to illustrate"
        " that we don't always want to have UI elements linger on screen while the app is"
        " re-rendering."
    )
    clean_slate = st.sidebar.checkbox(label="Use Clean Slate Rendering")

    st.title("A Multi-State App")
    st.info(
        "This is an app that allows the user to do multiple fundamentally different things. A"
        " choice the user makes early on in the flow will completely alter what is subsequently"
        ' rendered. We illustrate this by the "App State" `selectbox` below. Try changing its value'
        " and observe the re-rendering behaviour under the two different settings selectable in the"
        " sidebar."
    )
    app_state = st.selectbox(
        label="App State",
        options=["Logo State", "Text State", "Button State"],
    )

    default_slot = st.empty()

    if clean_slate:
        dg = get_clean_rendering_container(app_state=app_state)

        st.sidebar.success(
            "On re-running the same state: UI elements are allowed to linger, like normal.\n\n On"
            " state change: Notice that previous UI elements get cleaned up early.\n\n✅ This is"
            " desirable when we know up front that what is going to be rendered is fundamentally"
            " different from what was rendered before."
        )
        st.sidebar.warning(
            "⚠️ This re-rendering style is by no means default, and currently requires a lot of"
            " heavy lifting by the developer, as can be seen in the [source"
            " code](https://github.com/harahu/st-clean-slate-rendering) of this app.\n\nCan we get"
            " a simpler method for doing this? Something like:"
            " `st.experimental_wipe_old_ui_state()`\n\nWhere the call would send a message to the"
            " frontend asking it to disregard (for this single re-run) any UI elements lingering"
            " from the preceding render."
        )
    else:
        dg = default_slot.container()

        st.sidebar.error(
            "On state change: Notice that previous UI elements linger until they're replaced.\n\n❌"
            " We really only want this behaviour when the UI components being rendered are a"
            " continuation of what was displayed in the previous rendering. I.e. the new UI"
            ' elements are "the same as" the old UI elements. The ugliness of this behaviour is'
            " exacerbated in cases where re-running takes a long time, as that means the old UI"
            " elements linger for longer."
        )
        st.sidebar.info("ℹ️ This is the default behaviour of Streamlit apps.")

    if app_state == "Logo State":
        logo_state(dg=dg)
    elif app_state == "Text State":
        text_state(dg=dg)
    else:
        button_state(dg=dg)


if __name__ == "__main__":
    main()
