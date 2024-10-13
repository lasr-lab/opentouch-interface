from typing import Optional
from streamlit.delta_generator import DeltaGenerator
from opentouch_interface.interface.dataclasses.image.image import Image
from opentouch_interface.interface.options import DataStream
from opentouch_interface.interface.touch_sensor import TouchSensor
from opentouch.core.base.base_cnn import BaseCNN


class Model:
    """
    A model that integrates a CNN for touch-based image classification and displays the input/output
    through Streamlit UI. It reads input from a `TouchSensor`, processes it using a CNN, and shows
    the input image along with the model's prediction in a Streamlit interface.
    """

    def __init__(self, cnn: BaseCNN, sensor: TouchSensor):
        """
        Initialize the model with a CNN for prediction and a TouchSensor for input.

        :param cnn: The Convolutional Neural Network (CNN) used for image classification.
        :param sensor: The touch sensor that provides image data for classification.
        """
        self.cnn = cnn
        self.sensor = sensor
        self.reverse_label_mapping = {v: k for k, v in
                                      cnn.label_mapping.items()}  # Inverse mapping from label index to class name

        # Streamlit containers for displaying input/output images and labels
        self.container: Optional[DeltaGenerator] = None
        self.output_label: Optional[DeltaGenerator] = None
        self.output_area: Optional[DeltaGenerator] = None
        self.input_label: Optional[DeltaGenerator] = None
        self.input_area: Optional[DeltaGenerator] = None

    def update_container(self, container: DeltaGenerator):
        """
        Set up the Streamlit containers for displaying input and output.

        :param container: The main container in Streamlit where input/output will be displayed.
        """
        self.container = container

        # Prepare empty placeholders for input/output labels and areas
        self.output_label = container.empty()  # Placeholder for output label (e.g., prediction)
        self.output_area = container.container(border=True).empty()  # Area to display the prediction result

        self.input_label = container.empty()  # Placeholder for input label
        self.input_area = container.container(border=True).image([])  # Area to display the input image

    def render_output(self):
        """
        Display the CNN's prediction based on the current frame from the sensor.

        This method fetches a new frame from the sensor, processes it with the CNN, and
        displays the predicted label in the output area.
        """
        self.output_label.markdown('###### Prediction')
        if not self.sensor or not self.cnn:
            return

        # Read and process the sensor image, then predict using the CNN
        sample_image = self.sensor.read(DataStream.FRAME).as_tensor().unsqueeze(0).to(self.cnn.device)
        prediction = self.cnn.predict(sample_image)
        predicted_label = self.reverse_label_mapping.get(prediction.item(), "Unknown")

        # Display the predicted label
        self.output_area.text(f'Predicted label: {predicted_label}')

    def render_input(self):
        """
        Display the current input frame from the sensor.

        This method fetches the latest frame from the touch sensor and displays it in the input area.
        """
        self.input_label.markdown("###### Input Image")
        if not self.sensor or not self.cnn:
            return

        # Read the frame from the sensor
        frame: Image = self.sensor.read(DataStream.FRAME)
        if frame:
            # Convert the frame to OpenCV format and display it
            self.input_area.image(frame.as_cv2())
