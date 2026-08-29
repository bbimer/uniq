from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from enum import Enum


class TargetAspectRatio(Enum):
    ORIGINAL = "original"
    VERTICAL_9_16 = "9:16"      # 1080x1920 (Reels / TikTok / Shorts)
    SQUARE_1_1 = "1:1"          # 1080x1080 (Instagram Post)
    PORTRAIT_4_5 = "4:5"        # 1080x1350 (Instagram Portrait)
    LANDSCAPE_16_9 = "16:9"     # 1920x1080 (YouTube / Landscape)


@dataclass(frozen=True)
class ColorJitterConfig:
    enabled: bool = False
    brightness_range: Tuple[float, float] = (-0.015, 0.015)
    contrast_range: Tuple[float, float] = (0.98, 1.02)
    saturation_range: Tuple[float, float] = (0.98, 1.02)
    hue_range: Tuple[float, float] = (-0.5, 0.5)


@dataclass(frozen=True)
class ZoomConfig:
    enabled: bool = False
    min_percent: int = 100
    max_percent: int = 104


@dataclass(frozen=True)
class SpeedConfig:
    enabled: bool = False
    min_percent: int = 98
    max_percent: int = 102


@dataclass(frozen=True)
class Profile:
    """
    Декларативный профиль форматирования и трансформации медиа.
    """
    name: str
    target_ratio: TargetAspectRatio = TargetAspectRatio.ORIGINAL
    target_width: int = 1080
    target_height: int = 1920
    blur_background: bool = True
    color_jitter: ColorJitterConfig = field(default_factory=ColorJitterConfig)
    zoom: ZoomConfig = field(default_factory=ZoomConfig)
    speed: SpeedConfig = field(default_factory=SpeedConfig)
    filter_names: List[str] = field(default_factory=list)
    mute_audio: bool = False


# Предустановленные профили
REELS_TIKTOK_PROFILE = Profile(
    name="Reels / TikTok",
    target_ratio=TargetAspectRatio.VERTICAL_9_16,
    target_width=1080,
    target_height=1920,
    blur_background=True,
    color_jitter=ColorJitterConfig(enabled=True),
    zoom=ZoomConfig(enabled=True, min_percent=100, max_percent=104),
    speed=SpeedConfig(enabled=True, min_percent=98, max_percent=102),
)

SHORTS_PROFILE = Profile(
    name="YouTube Shorts",
    target_ratio=TargetAspectRatio.VERTICAL_9_16,
    target_width=1080,
    target_height=1920,
    blur_background=False,
    color_jitter=ColorJitterConfig(enabled=True),
    zoom=ZoomConfig(enabled=True, min_percent=100, max_percent=103),
    speed=SpeedConfig(enabled=True, min_percent=99, max_percent=101),
)

ORIGINAL_PROFILE = Profile(
    name="Original Format",
    target_ratio=TargetAspectRatio.ORIGINAL,
    target_width=0,
    target_height=0,
    blur_background=False,
)
