from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MediaType(Enum):
    VIDEO = "video"
    AUDIO = "audio"
    SUBTITLE = "subtitle"


@dataclass(frozen=True)
class VideoInfo:
    width: int
    height: int
    duration: float = 0.0
    fps: float = 0.0
    codec: str = ""
    pixel_format: str = "yuv420p"


@dataclass(frozen=True)
class AudioInfo:
    sample_rate: int = 44100
    channels: int = 2
    duration: float = 0.0
    codec: str = ""
    bitrate: int = 0


@dataclass(frozen=True)
class MediaInfo:
    path: str
    video: Optional[VideoInfo] = None
    audio: Optional[AudioInfo] = None

    @property
    def has_video(self) -> bool:
        return self.video is not None and self.video.width > 0 and self.video.height > 0

    @property
    def has_audio(self) -> bool:
        return self.audio is not None

    @property
    def duration(self) -> float:
        if self.video and self.video.duration > 0:
            return self.video.duration
        if self.audio and self.audio.duration > 0:
            return self.audio.duration
        return 0.0
