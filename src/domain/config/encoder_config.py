from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EncoderBackend(Enum):
    CPU = "cpu"
    NVIDIA = "nvidia"
    INTEL = "intel"
    AMD = "amd"
    APPLE = "apple"
    AUTO = "auto"


class EncoderPreference(Enum):
    """
    Политика выбора аппаратного ускорения:
    - AUTO: Выбрать лучший доступный энкодер (NVIDIA -> INTEL -> AMD -> APPLE -> CPU).
    - PREFERRED: Использовать указанный backend, если доступен. Если нет — fallback на CPU с предупреждением.
    - REQUIRED: Строго использовать указанный backend. Если недоступен — ошибка ENCODER_UNAVAILABLE.
    """
    AUTO = "auto"
    PREFERRED = "preferred"
    REQUIRED = "required"


@dataclass(frozen=True)
class EncoderConfig:
    """
    Чистая доменная конфигурация кодирования без привязки к флагам конкретного кодека FFmpeg.
    """
    backend: EncoderBackend = EncoderBackend.CPU
    preference: EncoderPreference = EncoderPreference.AUTO
    preset: str = "fast"
    quality: Optional[int] = 19
    bitrate_kbps: Optional[int] = None
    strip_metadata: bool = True
