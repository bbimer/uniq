# utils/ffmpeg_utils.py — Legacy Compatibility Layer
import os
import shutil
from typing import List, Optional, Tuple

from src.infrastructure.ffmpeg.probe_service import FFprobeService
from src.app.services.legacy_adapter import LegacyConfigAdapter
from src.app.services.render_service import RenderService
from .constants import FFMPEG_PATH

_probe_service = FFprobeService()
_render_service = RenderService(probe_service=_probe_service)

FFMPEG_PATH_EFFECTIVE = _render_service.runner.ffmpeg_bin


def has_audio_stream(video_path: str) -> bool:
    """Проверяет наличие аудио-дорожки в файле через FFprobeService."""
    try:
        info = _probe_service.inspect(video_path)
        return info.has_audio
    except Exception:
        return False


def get_video_dimensions(path: str) -> Tuple[int, int]:
    """Получает ширину и высоту видео с помощью FFprobeService."""
    try:
        info = _probe_service.inspect(path)
        if info.video:
            return info.video.width, info.video.height
        return 0, 0
    except Exception:
        return 0, 0


def process_single(
    in_path: str,
    out_path: str,
    filters: List[str],
    zoom_p: int,
    speed_p: int,
    overlay_file: Optional[str],
    overlay_pos: str,
    output_format: str,
    blur_background: bool,
    mute_audio: bool = False,
    strip_metadata: bool = False,
    hardware: str = "cpu",
    preset: str = "slow"
) -> None:
    """
    Тонкий адаптер обратной совместимости.
    Преобразует вызов в чистый доменный Job и исполняет через RenderService.
    """
    job = LegacyConfigAdapter.create_job(
        in_path=in_path,
        out_path=out_path,
        filters=filters,
        zoom_p=zoom_p,
        speed_p=speed_p,
        overlay_file=overlay_file,
        overlay_pos=overlay_pos,
        output_format=output_format,
        blur_background=blur_background,
        mute_audio=mute_audio,
        strip_metadata=strip_metadata,
        hardware=hardware,
        preset=preset
    )

    _render_service.render(job)
