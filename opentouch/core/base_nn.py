from abc import abstractmethod
from typing import Optional
from typing import Union, Dict

import torch
import torch.nn as nn
import torch.optim as optim
from torch import Tensor
from torch.utils.data import DataLoader

from opentouch.core.base_model import BaseModel


class BaseNeuralNetwork(BaseModel):
    """
    Abstract base class for neural networks, extending BaseModel.

    This class includes essential components such as model architecture, optimizer, and loss function.
    It also handles moving the model to the appropriate device (GPU/CPU) automatically.
    Subclasses should implement the `build` method to define their specific architecture.
    """

    def __init__(self) -> None:
        """Initializes the BaseNeuralNetwork with default attributes and device setup."""
        super().__init__()
        self.model: Optional[nn.Module] = None
        self.optimizer: Optional[optim.Optimizer] = None
        self.loss_fn: Union[nn.CrossEntropyLoss, nn.MSELoss, None] = None
        self.label_mapping: Optional[Dict[int, str]] = None
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # Check and set device
        self.to(self._device)  # Move model to the specified device

    @abstractmethod
    def build(self) -> None:
        """Defines the architecture of the model. Must be implemented in subclasses."""
        pass

    def fit(self, dataloader: DataLoader, num_epochs: int = 10, log_interval: int = 100) -> None:
        """
        General training function for neural networks.

        Args:
            dataloader (DataLoader): The data loader containing the training data.
            num_epochs (int): The number of epochs to train for.
            log_interval (int): The number of batches after which to log the training progress.
        """
        self.train()
        for epoch in range(num_epochs):
            running_loss: float = 0.0
            for i, (inputs, labels) in enumerate(dataloader):
                # Move data to device
                inputs: Tensor = inputs.to(self.device)
                labels: Tensor = labels.to(self.device)

                # Zero the parameter gradients
                self.optimizer.zero_grad()

                # Forward pass
                outputs: Tensor = self(inputs)
                loss: Tensor = self.loss_fn(outputs, labels)

                # Backward pass and optimization step
                loss.backward()
                self.optimizer.step()

                running_loss += loss.item()
                if (i + 1) % log_interval == 0:  # Log every `log_interval` batches
                    print(f"[Epoch {epoch + 1}, Batch {i + 1}] Loss: {running_loss / log_interval:.4f}")
                    running_loss = 0.0

        print("Training complete")

    def compile(self, optimizer: str = 'adam', learning_rate: float = 0.001, loss_fn: str = 'cross_entropy') -> None:
        """Compiles the model by setting the optimizer and loss function."""
        self.optimizer = self._get_optimizer(optimizer, learning_rate)
        self.loss_fn = self._get_loss_function(loss_fn)

    def _get_optimizer(self, optimizer: str, learning_rate: float) -> optim.Optimizer:
        """Returns the appropriate optimizer based on the string identifier."""
        if optimizer == 'adam':
            return optim.Adam(self.parameters(), lr=learning_rate)
        elif optimizer == 'sgd':
            return optim.SGD(self.parameters(), lr=learning_rate)
        else:
            raise ValueError(f"Unsupported optimizer: {optimizer}")

    @staticmethod
    def _get_loss_function(loss_fn: str) -> nn.Module:
        """Returns the appropriate loss function based on the string identifier."""
        if loss_fn == 'cross_entropy':
            return nn.CrossEntropyLoss()
        elif loss_fn == 'mse':
            return nn.MSELoss()
        else:
            raise ValueError(f"Unsupported loss function: {loss_fn}")

    @property
    def device(self) -> torch.device:
        """Returns the device used for computation (CPU or GPU)."""
        return self._device
