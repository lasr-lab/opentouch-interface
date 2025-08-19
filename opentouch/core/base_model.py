import json
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any

import torch
import torch.nn as nn


class BaseModel(nn.Module, ABC):
    """
    A base abstract class for all models, providing utility methods for metadata handling,
    model saving in ONNX format, and enforcing standard PyTorch model behavior.
    """

    def __init__(self):
        super().__init__()

    @property
    @abstractmethod
    def description(self) -> str:
        """Abstract property for a description of the model's purpose."""
        pass

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Constructs metadata with the basic attributes required for all models.

        Returns:
            dict: Metadata containing model_type and description.
        """
        return {
            'model_type': self.__class__.__name__,
            'description': self.description
        }

    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Abstract method that must be implemented to define the forward pass for the model.
        Args:
            x (torch.Tensor): Input tensor.
        Returns:
            torch.Tensor: Output tensor after passing through the model.
        """
        pass

    @abstractmethod
    def onnx_export(self) -> Dict[str, Any]:
        """
        Constructs the parameters needed for torch.onnx.export().

        Returns:
            dict: A dictionary containing the parameters needed for ONNX export.
        """
        pass

    def save(self, path: str) -> None:
        """
        Saves the model in ONNX format and stores it in a zip file along with metadata.

        Args:
            path (str): The path to save the model.
        """
        # Gather ONNX export parameters
        onnx_params = self.onnx_export()
        onnx_path = Path(path).with_suffix(".onnx")
        metadata_path = Path(path + "_metadata.json")

        # Perform the ONNX export using the current model (`self`)
        torch.onnx.export(
            self,
            onnx_params['example_input'],
            str(onnx_path),  # This is the required third argument - file path
            export_params=onnx_params.get('export_params', True),
            opset_version=onnx_params.get('opset_version', 17),
            input_names=onnx_params.get('input_names', ['input']),
            output_names=onnx_params.get('output_names', ['output']),
            # dynamic_axes=onnx_params.get('dynamic_axes', {'input': {0: 'batch_size'}}),
        )

        # onnx_program.save(str(onnx_path))  # Saves a file called onnx_path.onnx

        # Save metadata to a JSON file
        metadata = self.metadata
        metadata_path.write_text(json.dumps(metadata))

        # Zip ONNX model and metadata file
        zip_path = Path(path).with_suffix(".zip")
        with zipfile.ZipFile(zip_path, 'w') as model_zip:
            model_zip.write(onnx_path, onnx_path.name)
            model_zip.write(metadata_path, metadata_path.name)

        # Clean up temporary files
        onnx_path.unlink()
        metadata_path.unlink()
