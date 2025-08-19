from abc import abstractmethod
from typing import Dict, Any

from torch import Tensor

from opentouch.core.base_nn import BaseNeuralNetwork


class BaseCNN(BaseNeuralNetwork):
    """
    Base class for building Convolutional Neural Networks (CNNs) that supports both
    PyTorch and ONNX inference. Handles model construction, forward pass, prediction,
    and saving models in ONNX format with metadata.

    Attributes:
        input_channels (int): Number of input channels (e.g., 3 for RGB images).
        num_classes (int): Number of output classes for classification.
        label_mapping (dict, optional): Mapping from class indices to labels.
    """

    def __init__(self, label_mapping: dict, input_channels: int = 3) -> None:
        """Initialize the BaseCNN model."""
        super().__init__()
        self.input_channels: int = input_channels
        self.label_mapping: dict = label_mapping
        self.num_classes: int = len(label_mapping)
        self.build()  # Call the subclass's build method to define the architecture
        self.to(self.device)  # Move model to device (CPU or GPU)

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Constructs metadata with the basic attributes required for all models, including input channels,
        number of classes, label mapping and output type.
        """
        base_metadata = super().metadata
        base_metadata.update({
            'input_channels': self.input_channels,
            'num_classes': self.num_classes,
            'label_mapping': self.label_mapping,
            'output_type': 'classification'
        })
        return base_metadata

    @abstractmethod
    def build(self) -> None:
        """To be implemented in derived classes to define the model architecture."""
        pass

    @abstractmethod
    def preprocess(self, x: Tensor) -> Tensor:
        """
        Preprocesses the input tensor before it's fed into the model. This method can be overridden
        in subclasses for custom preprocessing.

        Args:
            x (Tensor): Input tensor.

        Returns:
            Tensor: Preprocessed input tensor.
        """
        return x

    def forward(self, x: Tensor) -> Tensor:
        """
        Forward pass of the model. Ensures the input tensor is processed and passed through
        the defined model. Raises an error if the model isn't built.

        Args:
            x (Tensor): Input tensor.

        Returns:
            Tensor: The output of the model after the forward pass.
        """
        if not self.model:
            raise NotImplementedError("The model is not defined. Implement build() in your subclass.")

        # Move input to the correct device
        x = x.to(self.device)

        # Preprocess input
        x = self.preprocess(x)

        return self.model(x)  # Forward pass through the model
