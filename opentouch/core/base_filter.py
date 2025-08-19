from typing import Dict, Any

import torch
from abc import abstractmethod

from opentouch.core.base_model import BaseModel


class BaseFilter(BaseModel):
    """
    A base abstract class for all filters, providing utility methods for metadata handling,
    filter saving in ONNX format, and enforcing standard PyTorch module behavior for filtering.
    """

    def __init__(self):
        super().__init__()

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Constructs metadata with the basic attributes required for all models, including input channels,
        number of classes, and output type.
        """
        base_metadata = super().metadata
        base_metadata.update({
            'output_type': 'image'
        })
        return base_metadata

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Abstract property for a description of the filter's purpose.
        """
        pass

    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Abstract method that must be implemented to define the forward pass for the filter.
        Args:
            x (torch.Tensor): Input tensor to be filtered.
        Returns:
            torch.Tensor: Output tensor after passing through the filter.
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
