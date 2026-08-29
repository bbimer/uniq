from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from src.domain.pipeline.pipeline import Pipeline
from src.domain.config.encoder_config import EncoderConfig


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """
    Задача на обработку одного медиа-файла.
    Поддерживает seed для полной детерминированности случайных эффектов.
    """
    id: str
    source_path: str
    target_path: str
    pipeline: Pipeline
    encoder: EncoderConfig = field(default_factory=EncoderConfig)
    overlay_path: Optional[str] = None
    seed: Optional[int] = None
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    error_message: Optional[str] = None
