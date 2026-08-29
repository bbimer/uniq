from enum import Enum
from typing import Optional


class ErrorCode(Enum):
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    PROBE_FAILED = "PROBE_FAILED"
    INVALID_GRAPH = "INVALID_GRAPH"
    ENCODER_UNAVAILABLE = "ENCODER_UNAVAILABLE"
    FFMPEG_EXECUTION_FAILED = "FFMPEG_EXECUTION_FAILED"
    CANCELLED = "CANCELLED"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class RenderError(Exception):
    """
    Структурированная ошибка процесса рендеринга.
    Позволяет UI и CLI получать типизированную причину сбоя без парсинга сырого stderr.
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        job_id: Optional[str] = None,
        cause: Optional[Exception] = None,
        details: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.job_id = job_id
        self.cause = cause
        self.details = details
        full_msg = f"[{code.value}] {message}"
        if job_id:
            full_msg = f"Job '{job_id}' failed: {full_msg}"
        super().__init__(full_msg)
