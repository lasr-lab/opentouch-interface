from typing import Type

import streamlit as st
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from opentouch_interface.core.payload import Payload
from opentouch_interface.core.registries.central_registry import CentralRegistry
from opentouch_interface.core.registries.class_registries import WidgetConfigRegistry
from opentouch_interface.dashboard.util.widget_state_manager import WidgetStateManager


class PayloadRenderer:
    def __init__(self, payload: Payload, group_idx: int):
        self._payload: Payload = payload
        self._group_idx: int = group_idx
        self._to_delete: list[str] = []  # Labels marked for deletion

        # Keeps the value of a widget even after switching pages. Used for the payload.
        self._state_manager = WidgetStateManager()

    def _has_unsaved_changes(self):
        if len(self._to_delete) > 0:
            return True

        for elem in self._payload.to_list():
            label = elem.get('label')
            if self._state_manager.get_state(label) != elem.get('default'):
                return True

        return False

    def render(self):
        # Populate the internal cache of the payload values. This must be done before showing the control buttons, so
        # self._has_unsaved_changes doesn't see any None values in the state cache
        for elem in self._payload.to_list():
            self._state_manager.init_state(elem.get('label'), elem.get('default'))

        # Top control buttons for add, save, and undo actions
        btn_width = 0.08
        spacing = 0.02
        add_col, _, save_col, undo_col = st.columns(
            [btn_width + spacing, 1 - 3 * btn_width - spacing, btn_width, btn_width])

        # Add Button with popover for adding new payload elements
        with add_col:
            with st.popover(label='', icon=':material/add_circle:', help='Add payload'):
                # Render the form for adding a new payload (details abstracted)
                self._render_add_payload()

        # Save Button to apply changes
        with save_col:
            def _save_changes():
                # Save changes and remove marked elements
                for widget_label in self._to_delete:
                    self._state_manager.remove_from_state_cache(widget_label)
                    self._payload.remove(widget_label)

                for element in self._payload.to_list():
                    element['default'] = self._state_manager.get_state(element['label'])

                self._to_delete.clear()
                CentralRegistry.update_container(value=True)
                st.empty()

            st.button(label='',
                      icon=':material/save:',
                      type='primary',
                      help='Save changes',
                      key=f'save_payload_{self._group_idx}',
                      use_container_width=True,
                      disabled=not self._has_unsaved_changes(),
                      on_click=_save_changes
                      )

        # Undo Button to revert unsaved changes
        with undo_col:
            def _undo_changes():
                # Clear the list of marked elements and reset the state cache
                self._to_delete.clear()
                for e in self._payload.to_list():
                    self._state_manager.set_state(e.get('label'), e.get('default'))

            st.button(label='',
                      icon=':material/replay:',
                      type='primary', help='Undo changes',
                      key=f'undo_payload_{self._group_idx}',
                      use_container_width=True,
                      disabled=not self._has_unsaved_changes(),
                      on_click=_undo_changes, args=()
                      )

        # Render all payload elements
        label_ratio = 0.93
        for elem in self._payload.to_list():
            elem_type = elem.get('type')
            label = elem.get('label')

            # Get widget function from streamlit
            widget_func = getattr(st, elem_type, None)
            if widget_func is None:
                continue

            # Build keyword arguments
            kwargs = {k: v for k, v in elem.items() if k not in ['type', 'default']}
            kwargs['label'] = label.upper()
            kwargs['key'] = self._state_manager.unique_key(label)
            kwargs['on_change'] = self._state_manager.sync_state_cache
            kwargs['args'] = (label,)

            with st.container():
                left, right = st.columns([label_ratio, 1 - label_ratio], vertical_alignment='bottom')

                # Render the input widget for the element
                with left:
                    widget_func(**kwargs)

                # Render the delete button for the element
                with right:
                    st.button(label='',
                              key=f'{self._state_manager.unique_key(label)}_rm',
                              type='secondary',
                              icon=':material/delete:',
                              use_container_width=True,
                              help='Delete',
                              disabled=label in self._to_delete,
                              on_click=self._to_delete.append,
                              args=(label,)
                              )
        st.empty()

    def render_widget_creation_form(self, config_cls: Type[BaseModel]) -> dict | None:
        """
        Render a Streamlit form based on the fields of the given Pydantic config class.
        Only the 'label' field is required; other fields are pre-populated with defaults.
        If available, the field description is used as a placeholder for text inputs.
        """

        fields = config_cls.model_fields
        form_values = {}

        with st.form(key=f'add_payload_form_{self._group_idx}', clear_on_submit=True, border=False):
            for field_name, field in fields.items():
                if field_name in ['type', 'horizontal']:
                    continue

                placeholder = field.description or f'Enter {field_name} (Type: {field.annotation})'

                # Label for input field
                label_text = field_name.capitalize()
                default_value = field.default

                # For integer fields, use st.number_input
                if field.annotation == float:
                    form_values[field_name] = st.number_input(
                        label=label_text,
                        value=float(default_value),
                        help=field.description,
                    )

                # For fields that are lists of strings, use a text input expecting a comma-separated list
                elif field.annotation == list[str]:
                    default_str = ', '.join(default_value) if default_value else ''
                    text_val = st.text_input(
                        label=f'{label_text} (comma separated)',
                        value=default_str,
                        placeholder=placeholder
                    )
                    form_values[field_name] = [s.strip() for s in text_val.split(',') if s.strip()]

                # For all other types, use a simple st.text_input
                else:
                    default_value = default_value if default_value != PydanticUndefined else ''
                    form_values[field_name] = st.text_input(
                        label=label_text,
                        value=default_value,
                        placeholder=placeholder
                    )

            submitted = st.form_submit_button('Add payload')
            if submitted:
                try:
                    form_values = {k: v for k, v in form_values.items() if v is not None}
                    config_obj = config_cls(**form_values)
                    return config_obj.model_dump()
                except Exception as e:
                    st.error(f'Configuration error: {e}')
        return None

    def _render_add_payload(self):
        # After a payload element was added, reset the selected payload type
        if 'payload_added' in st.session_state and st.session_state['payload_added']:
            st.session_state[f'add_payload_key_group_{self._group_idx}_ctype'] = None
            st.session_state['payload_added'] = False

        def format_widget_name(name: str) -> str:
            name = name.replace('_', ' ')
            return name.capitalize()

        original_names = WidgetConfigRegistry.get_widget_names()
        display_names = [format_widget_name(name) for name in original_names]

        ctype: str = st.selectbox(
            label='Select an input type',
            options=display_names,
            key=f'add_payload_key_group_{self._group_idx}_ctype',
            index=None
        )

        if not ctype:
            st.empty()  # Clear shadow elements if no type is selected
            return

        index = display_names.index(ctype)
        ctype = original_names[index]

        config_cls = WidgetConfigRegistry.get_config(ctype)
        config = self.render_widget_creation_form(config_cls)

        if config is not None:
            try:
                # Add the validated config to the payload
                self._payload.add(config=config)
                st.session_state['payload_added'] = True
                CentralRegistry.update_container(value=True)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add payload: {e}")
