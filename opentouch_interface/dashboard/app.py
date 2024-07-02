import streamlit as st

from opentouch_interface.dashboard.viewer.main_page import MainPage
from opentouch_interface.dashboard.viewer.sidebar import Sidebar
from opentouch_interface.dashboard.viewer.task_manager import TaskManager

st.set_page_config(
    page_title="Opentouch Viewer",
    page_icon="👌",
    initial_sidebar_state="expanded",
)

top = st.empty()
top_divider = st.empty()

top.title('Opentouch Viewer')
top_divider.divider()


def main():
    task_manager = TaskManager()
    sidebar = Sidebar()
    main_page = MainPage()

    task_manager.register(main_page.update_renderer, execute_once=True)
    task_manager.register(sidebar.render, execute_once=True)
    task_manager.register(main_page.render_viewers, execute_once=True)
    task_manager.register(main_page.render_frames, execute_once=False)

    task_manager.execute()


if __name__ == '__main__':
    main()
