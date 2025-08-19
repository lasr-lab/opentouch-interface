import os
import traceback

import streamlit as st
import yaml
from code_editor import code_editor
from streamlit.runtime.uploaded_file_manager import UploadedFile

from opentouch_interface.core.oti_config import OTIConfig
from opentouch_interface.core.registries.central_registry import CentralRegistry
from opentouch_interface.core.registries.class_registries import SensorFormRegistry
from opentouch_interface.core.sensor_group import SensorGroup
from opentouch_interface.core.sensor_group_saver import SensorGroupSaver
from opentouch_interface.dashboard.forms.sensor_form import SensorForm
from opentouch_interface.dashboard.viewers.viewer_group import ViewerGroup


class SensorRegistration:
    def __init__(self):
        self._container = st.container(border=False)
        _, self.center, _ = self._container.columns(spec=[0.2, 0.6, 0.2])

    def show(self):
        with self.center:
            st.title('Opentouch Viewer')
            st.divider()

            # Sensor selection dropdown menu
            sensor_type = st.selectbox(
                label="Add a new sensor to the dashboard",
                options=SensorFormRegistry.get_form_names(),
                index=None,
                placeholder="Select a sensor",
                label_visibility="visible",
                key='add_sensor_select_sensor_type'
            )

            if sensor_type:
                self._handle_manual_sensor_addition(sensor_type)
                self._show_message()
                return

            # Dataset selection dropdown menu
            def find_touch_files(path: str):
                touch_files = []
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith('.touch'):
                            full_path = os.path.join(root, file)
                            relative_path = os.path.relpath(full_path, path)
                            touch_files.append(relative_path)
                return touch_files

            base_directory = OTIConfig.get_base_directory()
            datasets = find_touch_files(base_directory)

            dset_name = st.selectbox(
                label="Select a dataset",
                options=datasets,
                index=None,
                placeholder="Select a dataset",
                label_visibility="visible",
                key='add_sensor_select_dataset',
                help=f'Select one dataset located under {base_directory}'
            )

            if dset_name:
                self._handle_dataset_addition(dset_name)
                self._show_message()
                return

            # File upload menu
            self._handle_file_upload_sensor_addition()
            self._show_message()

    def _handle_dataset_addition(self, path: str):
        if yaml_config := SensorGroupSaver.read_config(path):
            yaml_config['_method'] = 'dataset'
            yaml_config['source'] = path

        else:
            st.session_state['add_sensor_message'] = {'message': f'Could not load configuration from {path}',
                                                      'fail': True}

        # Add sensor button
        st.button(
            label="Add sensor",
            type="primary",
            disabled=not yaml_config,
            on_click=self.add_group,
            args=(yaml_config,)
        )

    def _handle_manual_sensor_addition(self, sensor_type: str) -> None:
        """Handle manually adding a sensor via form input."""
        form: SensorForm = self.render_input_fields(sensor_type=sensor_type)

        yaml_config: dict[str, str] | None = None
        if form.is_filled():
            yaml_config = form.to_dict()
            yaml_config['_method'] = 'form'

        # Add sensor button
        st.button(
            label="Add sensor",
            type="primary",
            disabled=not yaml_config,
            on_click=self.add_group,
            args=(yaml_config,)
        )

    def _handle_file_upload_sensor_addition(self) -> None:
        """Handle sensor addition via YAML file upload."""

        # Hacky solution to clear buffer of a file uploader
        # https://discuss.streamlit.io/t/are-there-any-ways-to-clear-file-uploader-values-without-using-streamlit-form/40903/2
        if 'add_sensor_fu_key' not in st.session_state:
            st.session_state['add_sensor_fu_key'] = 0

        file: UploadedFile = st.file_uploader(
            label="Or choose sensor config",
            type=['yaml'],
            accept_multiple_files=False,
            label_visibility="collapsed",
            key=f'add_sensor_fu_index_{st.session_state["add_sensor_fu_key"]}'
        )

        if file:
            # Display code editor if it's a YAML file
            self._process_yaml_file(file)

        else:
            # Display info message if no sensors are added
            if not CentralRegistry.viewer_group_registry().viewer_count:
                self._show_info_message()

    def _process_yaml_file(self, file: UploadedFile) -> None:
        """Process and update the YAML file before adding sensor."""
        content = file.read().decode("utf-8")
        response = code_editor(content, lang="yaml")

        left, right = st.columns(2)
        has_error, updated_config = self._parse_yaml(response['text'] or content)

        with right:
            if has_error:
                st.error("Invalid YAML format.")
            # else:
            #     st.success("Updated your sensor config.")

        with left:
            st.info(body="Press Ctrl+Return to save your changes", icon="💡")

            if updated_config:
                updated_config['_method'] = 'upload'

            st.button(
                label="Add sensor",
                type="primary",
                disabled=not updated_config,
                use_container_width=True,
                on_click=self.add_group,
                args=(updated_config,)
            )

    @staticmethod
    def _parse_yaml(content: str) -> (bool, dict | None):
        """Parse YAML content, returning if there was an error and the parsed config."""
        try:
            return False, yaml.safe_load(content)
        except yaml.YAMLError:
            return True, None

    @staticmethod
    def _show_info_message() -> None:
        """Show an info message if no sensors are added."""
        st.info(
            body="To add a new sensor to the 'Live View' page, you can either manually enter the sensor "
                 "details, upload a YAML config or select a dataset for replay.",
            icon="💡"
        )

    @staticmethod
    def render_input_fields(sensor_type: str) -> SensorForm:
        form_cls = SensorFormRegistry.get_form(sensor_type)
        if form_cls is None:
            raise ValueError(f"Unsupported sensor form: {form_cls} is not a registered sensor form class")
        return form_cls().render()

    @staticmethod
    def add_group(config: dict[str, str]):
        try:
            sensor_group = SensorGroup(config=config)
            viewer_group: ViewerGroup = ViewerGroup(sensor_group=sensor_group)

            # Output message
            message = '\n'.join(
                f'- {viewer.sensor.get("sensor_name")} ({viewer.sensor.get("sensor_type")}) \n'
                for viewer in viewer_group.viewers)

            # Save the success message in the session state so it can be displayed in-order at a later point. st.success
            # won't work here because callbacks process first, causing the success message to render prematurely
            # (see https://docs.streamlit.io/develop/concepts/architecture/widget-behavior#order-of-operations)
            st.session_state['add_sensor_message'] = {'group_name': viewer_group.group_name, 'message': message}

            # Clear user input after the group has been added
            if isinstance(config, dict):
                st.session_state['add_sensor_select_sensor_type'] = None
                st.session_state['add_sensor_fu_key'] += 1

        except Exception:  # noqa
            full_trace = traceback.format_exc()
            st.session_state['add_sensor_message'] = {'message': full_trace, 'fail': True}

    @staticmethod
    def _show_message():
        if 'add_sensor_message' in st.session_state:
            message = st.session_state.pop('add_sensor_message')

            fail = message.get('fail', False)
            if not fail:
                st.success(
                    body=f"The following sensors have been successfully added as part of the group "
                         f"**{message['group_name']}**:\n\n{message['message']}",
                    icon="💡"
                )
            else:
                st.error(body=message['message'], icon="⚠️")


sensor_registration = SensorRegistration()
sensor_registration.show()
