import torch
from tqdm import tqdm
import numpy as np
from torch import nn
from torch.utils.data import (Dataset, DataLoader)
from torch.optim import Optimizer
from torch.nn import Module, Module as LossFunction
from torch import Tensor

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from typing import (
    Any,
    Callable,
    List,
    Optional,
    Tuple,
    Union,
    Dict
)

class CustomDataset(Dataset):
    """
    A custom dataset class for handling data and corresponding labels. 

    This class inherits from PyTorch's `Dataset` and allows the option to apply 
    transformations on the data samples.

    Attributes
    ----------
    data : Union[List[Any], np.ndarray, torch.Tensor]
        List, array, or tensor of data samples.
    labels : Union[List[Any], np.ndarray, torch.Tensor]
        Corresponding labels for the data samples.
    transform : Optional[Callable]
        A callable function or transformation to apply to each data sample.

    Methods
    -------
    __len__()
        Returns the total number of samples in the dataset.
    __getitem__(idx: int)
        Retrieves a sample and its label by index, applying transformation if available.
    """

    def __init__(
        self, 
        data: Union[List[Any], torch.Tensor], 
        labels: Union[List[Any], torch.Tensor], 
        transform: Optional[Callable] = None
    ) -> None:
        """
        Initializes the dataset with data samples and labels, along with an optional transform.

        Parameters
        ----------
        data : Union[List[Any], torch.Tensor]
            List or tensor of data samples.
        labels : Union[List[Any], torch.Tensor]
            Corresponding labels for the data samples.
        transform : Optional[Callable], optional
            Optional transformation to be applied to the data samples, by default None.
        """
        self.data = data
        self.labels = labels
        self.transform = transform

    def __len__(self) -> int:
        """
        Returns the total number of samples in the dataset.

        Returns
        -------
        int
            Number of samples in the dataset.
        """
        return len(self.data)

    def __getitem__(self, idx: int) -> Tuple[Any, Any]:
        """
        Retrieves a sample and its corresponding label by index.

        Parameters
        ----------
        idx : int
            Index of the sample and label to retrieve.

        Returns
        -------
        Tuple[Any, Any]
            A tuple containing the data sample and its corresponding label.

        Notes
        -----
        If the `labels` attribute is `None`, only the sample is returned.
        """
        sample = self.data[idx]
        label = self.labels[idx] if self.labels is not None else None

        if self.transform:
            sample = self.transform(sample)

        return (sample, label) if label is not None else sample

class Trainer:
    """
    Custom trainer class for training and validating a PyTorch model.
    """
    def __init__(self, model, train_loader, val_loader, optimizer, criterion, device):
        """
        Initializes the Trainer class.

        Args:
            model (torch.nn.Module): The PyTorch model to be trained.
            train_loader (torch.utils.data.DataLoader): DataLoader for the training dataset.
            val_loader (torch.utils.data.DataLoader): DataLoader for the validation dataset.
            optimizer (torch.optim.Optimizer): Optimizer for the training process (e.g., Adam, SGD).
            criterion (torch.nn.Module): Loss function for calculating the loss.
            device (torch.device): Device to run the computations (either 'cpu' or 'cuda').
        """
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.optimizer = optimizer
        self.criterion = criterion
        self.device = device
        self.trainLoss = {}
        self.valLoss = {}

    def train(self, num_epochs):
        """
        Trains the model for a given number of epochs with a single progress bar.

        Args:
            num_epochs (int): Number of epochs to train the model.
        """
        # Create a single progress bar for all epochs
        progress_bar = tqdm(total=num_epochs, desc="Training Progress", position=0, leave=True)

        for epoch in range(1, num_epochs + 1):
            # Set the model to training mode
            self.model.train()
            total_loss = 0

            for batch in self.train_loader:
                inputs, targets = batch
                inputs, targets = inputs.to(self.device), targets.to(self.device)

                # Forward pass
                predictions = self.model(inputs)
                loss = self.criterion(predictions, targets)

                # Backward pass and optimization
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

                total_loss += loss.item()

            avg_loss = total_loss / len(self.train_loader)
            self.trainLoss[epoch] = avg_loss

            # Validation step
            val_loss = self.validate(epoch)
            self.valLoss[epoch] = val_loss

            # Update the progress bar with epoch number and losses
            progress_bar.set_description(f"Epoch {epoch}/{num_epochs} | Train Loss: {avg_loss:.4f} | Val Loss: {val_loss:.4f}")
            progress_bar.update(1)

        progress_bar.close()
        return self.trainLoss, self.valLoss

    def validate(self, epoch):
        """
        Validates the model after each epoch.

        Args:
            epoch (int): The current epoch number.

        Returns:
            float: Average validation loss for the epoch.
        """
        self.model.eval()
        total_val_loss = 0

        with torch.no_grad():
            for batch in self.val_loader:
                inputs, targets = batch
                inputs, targets = inputs.to(self.device), targets.to(self.device)

                # Forward pass
                outputs = self.model(inputs)
                val_loss = self.criterion(outputs, targets)
                total_val_loss += val_loss.item()

        avg_val_loss = total_val_loss / len(self.val_loader)
        return avg_val_loss

class LinearRegression(Module):
    """
    A simple linear regression model implemented with PyTorch.

    Attributes
    ----------
    w : torch.Tensor
        Weights for the linear regression model.
    b : torch.Tensor
        Bias for the linear regression model.

    Methods
    -------
    forward(X: torch.Tensor) -> torch.Tensor
        Performs a forward pass (predicts the output for input X).
    """

    def __init__(self, in_dims: int, out_dims: int = 1):
        """
        Initializes the LinearRegression model with random weights and bias.

        Parameters
        ----------
        in_dims : int
            Number of input features (dimension of the input).
        out_dims : int, optional
            Number of output features (default is 1 for basic regression).
        """
        super(LinearRegression, self).__init__()

        self.linear = nn.Linear(in_dims, out_dims, bias=True)

    def forward(self, X: Tensor) -> Tensor:
        """
        Performs the forward pass through the linear regression model.

        Parameters
        ----------
        X : torch.Tensor
            Input tensor of shape (batch_size, in_dims).

        Returns
        -------
        torch.Tensor
            Predicted output tensor of shape (batch_size, out_dims).
        """
        return self.linear(X)

class LogisticRegression(LinearRegression):
    """
    A simple logistic regression model implemented with PyTorch, inheriting from the `LinearRegression` class.

    Attributes
    ----------
    w : Tensor
        Weights of the logistic regression model.
    b : Tensor
        Bias term of the logistic regression model.
    multinomial : bool
        Indicates whether the model is for binary or multinomial classification.

    Methods
    -------
    forward(X: Tensor) -> Tensor
        Performs a forward pass and outputs probabilities.
    """ 
    def __init__(self, in_dims: int, out_dims: int = 1, multinomial: bool = False):
        """
        Initializes the LogisticRegression model with random weights and bias.

        Parameters
        ----------
        in_dims : int
            Number of input features (dimension of the input).
        out_dims : int, optional
            Number of output features. For binary classification, this is usually 1. Default is 1.
        multinomial : bool
            Indicates whether the model is for binary or multinomial classification.
        """
        if multinomial and out_dims < 2:
            raise ValueError("For multinomial classification, out_dims must be at least 2.")
        if not multinomial and out_dims != 1:
            raise ValueError("For binary classification, out_dims must be 1.")
        
        self.multinomial = multinomial
        super().__init__(in_dims, out_dims)

    def forward(self, X: Tensor) -> Tensor:
        """
        Performs the forward pass through the logistic regression model.

        Parameters
        ----------
        X : Tensor
            Input tensor of shape (batch_size, in_dims).

        Returns
        -------
        Tensor
            Predicted probabilities:
            - For binary classification, shape is (batch_size, 1), with probabilities for the positive class.
            - For multinomial classification, shape is (batch_size, out_dims), with probabilities over all classes.
        """
        logits = super().forward(X)

        if self.multinomial:
            return torch.softmax(logits, dim=1)  # Normalize along the class dimension
        
        return torch.sigmoid(logits)
    
class LinearSVM(LinearRegression):
    def __init__(self, in_dims: int) -> None:
        super().__init__(in_dims)

    def forward(self, X: torch.Tensor) -> Tensor:
        return super().forward(X)

    def hinge_loss(self, y_pred: Tensor, y_true: Tensor) -> Tensor:
        """
        Computes the hinge loss.
        
        Parameters
        ----------
        y_pred : torch.Tensor
            Predicted values from the model.
        
        y_true : torch.Tensor
            True labels (+1 or -1).

        Returns
        -------
        torch.Tensor
            Computed hinge loss.
        """
        return torch.mean(torch.clamp(1 - y_pred * y_true, min=0))