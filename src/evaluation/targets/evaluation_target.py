"""Implement base Evaluation Target class."""

from abc import ABC, abstractmethod


class EvaluationTarget(ABC):
    """Base Evaluation Target abstract class."""

    @abstractmethod
    def __call__(self, **kwargs):
        """Implement the main function to be called by the Evaluation SDK."""
        pass
