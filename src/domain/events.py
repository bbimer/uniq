import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, List
from src.domain.errors import RenderError


class JobEventType(Enum):
    QUEUED = "QUEUED"
    STARTED = "STARTED"
    PROGRESS = "PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BATCH_COMPLETED = "BATCH_COMPLETED"


@dataclass(frozen=True)
class JobEvent:
    """
    Единое доменное событие жизненного цикла задачи или пакета.
    Используется CLI, GUI (Qt), логированием и мониторингом.
    """
    event_type: JobEventType
    job_id: str
    progress: float = 0.0
    error: Optional[RenderError] = None
    message: str = ""
    timestamp: float = field(default_factory=time.time)

    def __repr__(self) -> str:
        err_str = f", error={self.error.code.value}" if self.error else ""
        return f"JobEvent({self.event_type.value}, job='{self.job_id}', p={self.progress:.1%}{err_str})"


class EventBus:
    """Потокобезопасная шина событий для подписки на жизненный цикл задач."""

    def __init__(self):
        self._subscribers: List[Callable[[JobEvent], None]] = []

    def subscribe(self, callback: Callable[[JobEvent], None]) -> None:
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[JobEvent], None]) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def publish(self, event: JobEvent) -> None:
        for sub in list(self._subscribers):
            try:
                sub(event)
            except Exception:
                pass
