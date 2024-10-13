from abc import abstractmethod, ABC
from typing import Optional

from streamlit.delta_generator import DeltaGenerator
from opentouch_interface.core.sensors.touch_sensor import TouchSensor


class BaseImageViewer(ABC):
    """
    Abstract base class for viewers that display sensor data in a Streamlit interface.

    The `BaseImageViewer` provides the basic structure for creating sensor viewers that interact with
    a `TouchSensor`. Subclasses should implement the `render_options` and `render_frame` methods
    to define how options and sensor data are displayed.
    """

    def __init__(self, sensor: TouchSensor):
        """
        Initializes the BaseImageViewer with a sensor and prepares placeholders for UI components.

        :param sensor: The sensor instance associated with this viewer.
        :type sensor: TouchSensor
        """
        self.sensor: TouchSensor = sensor
        self.sensor_name: str = self.sensor.config.sensor_name

        # Streamlit containers for rendering components
        self.container: Optional[DeltaGenerator] = None
        self.title: Optional[DeltaGenerator] = None
        self.left: Optional[DeltaGenerator] = None
        self.right: Optional[DeltaGenerator] = None
        self.image_widget: Optional[DeltaGenerator] = None

    @abstractmethod
    def render_options(self) -> None:
        """
        Abstract method to render viewer-specific options in the UI.

        Subclasses must implement this method to provide a way for users to adjust settings or parameters
        for the specific type of viewer.
        """
        pass

    @abstractmethod
    def render_frame(self) -> None:
        """
        Abstract method to render the current frame of sensor data.

        Subclasses must implement this method to display the sensor's data (e.g., images or other visualizations)
        in the `image_widget` or other UI components.
        """
        pass

    def update_container(self, container: DeltaGenerator) -> None:
        """
        Updates the container for rendering frames and UI components, setting up layout for the viewer.

        This method sets up the layout using columns and containers for the image widget and other components.

        :param container: A `DeltaGenerator` container from Streamlit, used to display the viewer.
        :type container: DeltaGenerator
        """
        self.container = container.container(border=True)
        self.title = self.container.empty()
        self.left, self.right = self.container.columns(2)
        self.image_widget = self.left.image([])
