from typing import Dict

import pkg_resources
import streamlit as st
from opentouch.core.base.base_cnn import BaseCNN
from streamlit.runtime.uploaded_file_manager import UploadedFile

from opentouch_interface.dashboard.models.model import Model
from opentouch_interface.dashboard.models.model_registry import ModelRegistry
from opentouch_interface.dashboard.viewers.group_registry import GroupRegistry
from opentouch_interface.core.sensors.touch_sensor import TouchSensor


class AddModel:
    """
    A UI component for adding models to the registry in the Streamlit interface.
    This class allows users to upload a pre-trained model, select a sensor, and
    register the model for use in inference.
    """

    def __init__(self):
        """
        Initialize the AddModel component, displaying the UI header and divider.
        """
        # Create a container for the UI components
        self.container = st.container()

        # Display the title and a dividing line in the Streamlit container
        with self.container:
            st.title("Model Registry")
            st.divider()

    def show(self):
        """
        Display the UI elements to upload a model, select a sensor, and add the model to the registry.

        The method handles the model upload process, shows a dropdown to select an available sensor,
        and registers the model with the selected sensor upon clicking the 'Add model' button.
        """
        # Retrieve a dictionary of connected sensors
        sensors = self._get_sensor_dict()

        # Upload a pre-trained model file
        model = self._upload_model()

        # Dropdown to select a sensor for inference, disabled if no model is uploaded
        selected_sensor = sensors.get(
            st.selectbox(
                label="Select the data source",
                options=list(sensors.keys()),
                placeholder="Select a sensor",
                label_visibility="visible",
                disabled=not model
            ), None
        )

        # Button to add the model-sensor pair, disabled if no model or sensor is selected
        if st.button(label="Add model", type="primary", disabled=not (model and selected_sensor)):
            self._register_model(model, selected_sensor)
            st.divider()
            st.success(body="Model has been successfully added.", icon="💡")

        # Display info if no sensors are connected
        if not sensors:
            st.divider()
            st.info(body="No connected sensors found. Please add one on the 'Add Sensor' page.", icon="💡")

    @staticmethod
    def _register_model(file: UploadedFile, sensor: TouchSensor):
        """
        Register the uploaded model by linking it with the selected sensor.

        :param file: The uploaded pre-trained model file.
        :param sensor: The selected TouchSensor to associate with the model.
        """
        model_registry: ModelRegistry = st.session_state.model_registry
        model = Model(cnn=BaseCNN.load(file), sensor=sensor)  # Create a Model object from the uploaded file and sensor
        model_registry.add_model(model)  # Add the model to the registry

    @staticmethod
    def _upload_model():
        """
        Handle the model file upload in the Streamlit UI.

        :return: The uploaded model file (UploadedFile), or None if no file is uploaded.
        """
        return st.file_uploader(label="Upload your pre-trained model", type=['zip'], accept_multiple_files=False)

    @staticmethod
    def _get_sensor_dict() -> Dict[str, TouchSensor]:
        """
        Retrieve a dictionary mapping sensor names to TouchSensor objects.

        :return: A dictionary where the keys are sensor names and the values are TouchSensor instances.
        """
        group_registry: GroupRegistry = st.session_state.group_registry
        return {
            f'Sensor name: {viewer.sensor_name}, Group name: {group.group_name}': viewer.sensor
            for group in group_registry.groups  # Iterate through all groups in the registry
            for viewer in group.viewers  # Iterate through all viewers in each group
        }


# Check if PyTorch is installed; if not, provide installation instructions
if "torch" not in {pkg.key for pkg in pkg_resources.working_set}:
    st.error("PyTorch is not installed. Please install it using the following command:")
    st.code("pip install torch")

# Create and display the AddModel UI
add_model = AddModel()
add_model.show()
