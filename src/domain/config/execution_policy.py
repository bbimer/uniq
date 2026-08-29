from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ExecutionPolicy:
    """
    Политика выполнения пакетных задач.
    Определяет лимиты параллелизма, тайм-ауты и стратегию обработки ошибок.
    """
    max_concurrent_jobs: int = 2
    allow_fallback_to_cpu: bool = True
    stop_on_first_error: bool = False
    timeout_seconds: Optional[float] = None
