from typing import List
from streamlit.delta_generator import DeltaGenerator
from opentouch_interface.dashboard.models.model import Model
from opentouch_interface.dashboard.util.util import get_clean_rendering_container


class ModelRegistry:
    """
    Manages a registry of models, providing methods to add models and render their input/output in Streamlit.

    This class holds multiple models, allowing their inputs and outputs to be displayed in a single Streamlit
    interface. It supports adding models to the registry and renders the input images and predictions
    for each model.
    """

    def __init__(self):
        """
        Initializes an empty registry to store multiple models.
        """
        self.models: List[Model] = []

    @property
    def model_count(self) -> int:
        """
        Returns the count of registered models.

        :return: The number of models currently in the registry.
        """
        return len(self.models)

    def add_model(self, model: Model) -> None:
        """
        Adds a new model to the registry.

        :param model: The model to be added, which will be tracked by the registry.
        """
        self.models.append(model)

    def render(self) -> None:
        """
        Renders input and output for all registered models using a clean Streamlit container.

        This method prepares a clean Streamlit container and iterates over each registered model to
        render their input images and output predictions. It continuously updates the display for
        real-time data visualization.
        """
        # Get a clean Streamlit container for rendering models
        clean_container: DeltaGenerator = get_clean_rendering_container().container()

        # Initialize each model's Streamlit container
        for model in self.models:
            model.update_container(container=clean_container)

        # Continuously render input and output for each model
        while len(self.models) > 0:
            for model in self.models:
                model.render_input()  # Render the input image from the sensor
                model.render_output()  # Render the model's prediction
