import numpy as np
import onnxruntime as ort
from streamlit.delta_generator import DeltaGenerator

from opentouch_interface.core.registries.central_registry import CentralRegistry
from opentouch_interface.core.sensors.touch_sensor import TouchSensor


class Model:
    """
    A model that integrates a CNN for touch-based sensors classification and displays the input/output
    through Streamlit UI. It reads input from a `TouchSensor`, processes it using a CNN, and shows
    the input sensors along with the model's prediction in a Streamlit interface.
    """

    def __init__(self, session: ort.InferenceSession, sensor: TouchSensor):
        if not hasattr(session, "model_type") or not isinstance(session.model_type, str):
            raise ValueError("Model type is not set for session")

        self.session: ort.InferenceSession = session
        self.sensor = sensor

        # Streamlit containers for displaying input/output images and labels
        self.container: DeltaGenerator | None = None
        self.button_container: DeltaGenerator | None = None
        self.output_label: DeltaGenerator | None = None
        self.output_area: DeltaGenerator | None = None
        self.input_label: DeltaGenerator | None = None
        self.input_area: DeltaGenerator | None = None

        self._key_prefix: str = f'{CentralRegistry.model_registry().model_count}_'

    def update_container(self, container: DeltaGenerator):
        """Set up Streamlit containers."""
        self.container = container
        self.button_container = container.container(border=False)
        self.input_label, self.output_label = [c.empty() for c in self.container.columns(2, border=False)]
        self.input_area, self.output_area = [c.empty() for c in self.container.columns(2, border=True)]

    def render(self):
        self.render_input()
        self.render_output()

    def render_button(self):
        """Render remove button."""
        self.button_container.button(
            "Remove model",
            on_click=CentralRegistry.model_registry().remove_model,
            args=(self,),
            key=f'{self._key_prefix}_remove_model_key'
        )

    def render_output(self):
        """Generic output rendering - input handling is user's responsibility."""
        self.output_label.markdown('###### Output')

        # Check for the presence of the sensor and session
        if not (self.sensor and self.session):
            return

        try:
            # Step 1: Get sensor data (assume user knows what they're doing)
            sample_data = self.sensor.read(path='camera', projection='camera', count=1)['camera'][0]

            # Step 2: Simple preprocessing (just add batch dimension)
            input_batch = np.expand_dims(sample_data, axis=0)

            # Step 3: Run inference
            input_name = self.session.get_inputs()[0].name
            output_name = self.session.get_outputs()[0].name
            prediction = self.session.run([output_name], {input_name: input_batch})[0]

            # Step 4: Display based on output type
            self._display_prediction(prediction)

        except Exception as e:
            self.output_area.error(f"Error: {str(e)}")

    def _display_prediction(self, prediction: np.ndarray):
        """Display prediction based on output_type."""
        output_type = getattr(self.session, 'output_type', 'raw')

        if output_type == 'classification':
            self._display_classification(prediction)
        elif output_type == 'image':
            self._display_image(prediction)
        else:
            self._display_raw(prediction)

    def _display_classification(self, prediction: np.ndarray):
        """Display classification results with labels and confidence."""
        predicted_class = np.argmax(prediction[0])
        confidence = np.max(prediction[0])

        if hasattr(self.session, 'label_mapping') and self.session.label_mapping:
            predicted_label = self.session.label_mapping[str(predicted_class)]
            result = f"**Prediction:** {predicted_label}"
        else:
            result = f"**Class:** {predicted_class}\n**Confidence:** {confidence:.1%}"

        self.output_area.markdown(result)

    def _display_image(self, prediction: np.ndarray):
        """Display image output (e.g., segmentation, generation)."""

        img = np.squeeze(prediction)
        self.output_area.image(img, caption="Model Output")

    def _display_raw(self, prediction: np.ndarray):
        """Display raw output info when type is unknown."""
        pred = np.squeeze(prediction)

        result = f"""
        **Raw Output:**
        - **Shape:** {pred.shape}
        - **Type:** {pred.dtype}
        - **Range:** [{pred.min():.3f}, {pred.max():.3f}]
        """

        # Show some sample values
        flat = pred.flatten()
        if len(flat) <= 10:
            result += f"- **Values:** {flat.tolist()}"
        else:
            result += f"- **First 5:** {flat[:5].tolist()}"

        self.output_area.markdown(result)

    def render_input(self):
        """Display current input - assume it's image data."""
        self.input_label.markdown("###### Input")
        if not self.sensor or not self.session:
            return

        try:
            data = self.sensor.read(path='camera', projection='camera', count=1)
            frame = data['camera'][0] if data.get('camera') else None
            if frame is not None:
                self.input_area.image(frame, caption='Model Input')
        except Exception as e:
            self.input_area.error(f"Input display error: {str(e)}")
