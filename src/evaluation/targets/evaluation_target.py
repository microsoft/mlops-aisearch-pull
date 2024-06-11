from abc import ABC, abstractmethod


class EvaluationTarget(ABC):

    @abstractmethod
    def __call__(self, **kwargs):
        pass
