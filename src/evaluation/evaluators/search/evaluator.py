"""Implement base Evaluator class for the Promptflow-Eval SDK."""

from abc import ABC, abstractmethod


class Evaluator(ABC):
    """
    Base Evaluator abstract class
    """

    @abstractmethod
    def __call__(self, **kwargs):
        """
        Implements the main function to be called by the Evaluation SDK.
        """
        pass
