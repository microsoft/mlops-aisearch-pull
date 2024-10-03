"""Implement base Evaluator class."""

from abc import ABC, abstractmethod


class Evaluator(ABC):
    """Base Evaluator abstract class."""

    @abstractmethod
    def __call__(self, **kwargs):
        """Implement the main function to be called by the Evaluation SDK."""
        pass
