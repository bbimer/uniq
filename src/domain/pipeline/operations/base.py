from abc import ABC, abstractmethod
from src.domain.pipeline.graph.nodes import StreamRef
from src.domain.pipeline.graph.graph_context import GraphContext


class Operation(ABC):
    """Базовый абстрактный класс операции над медиа-потоком."""
    pass


class VideoOperation(Operation, ABC):
    """Операция трансформации одного видео-потока."""

    @abstractmethod
    def apply(self, graph: GraphContext, video_in: StreamRef) -> StreamRef:
        """
        Применяет трансформацию к входному видео-потоку в рамках GraphContext
        и возвращает результирующий видео-поток.
        """
        pass


class AudioOperation(Operation, ABC):
    """Операция трансформации одного аудио-потока."""

    @abstractmethod
    def apply(self, graph: GraphContext, audio_in: StreamRef) -> StreamRef:
        """
        Применяет трансформацию к входному аудио-потоку в рамках GraphContext
        и возвращает результирующий аудио-поток.
        """
        pass
