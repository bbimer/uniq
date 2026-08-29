import os
import pytest
from src.app.services.legacy_adapter import LegacyConfigAdapter
from src.app.services.render_service import RenderService
from src.infrastructure.ffmpeg.probe_service import FFprobeService


def test_reels_blur_background_structural(synthetic_video, tmp_path):
    """Проверка structural equivalence для трансформации Reels с размытием фона."""
    out_path = os.path.join(tmp_path, "out_reels.mp4")

    job = LegacyConfigAdapter.create_job(
        in_path=synthetic_video,
        out_path=out_path,
        filters=["Случ. цвет (яркость/контраст/...)"],
        zoom_p=102,
        speed_p=102,
        overlay_file=None,
        overlay_pos="Середина-Центр",
        output_format="Reels/TikTok (1080x1920)",
        blur_background=True,
        mute_audio=False,
        strip_metadata=True,
        preset="ultrafast"
    )

    render_service = RenderService()
    render_service.render(job)

    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0

    # Проверяем структурные параметры через FFprobe
    probe = FFprobeService()
    info = probe.inspect(out_path)

    assert info.has_video
    assert info.video.width == 1080
    assert info.video.height == 1920
    assert info.video.pixel_format == "yuv420p"
    assert info.video.codec == "h264"
    assert info.has_audio
    assert info.audio.codec == "aac"
    # Длительность должна быть ~ 2 / 1.02 ≈ 1.96 сек
    assert 1.8 <= info.duration <= 2.2


def test_original_format_speed_and_color_structural(synthetic_video, tmp_path):
    """Проверка structural equivalence для оригинального формата со сменой скорости."""
    out_path = os.path.join(tmp_path, "out_orig.mp4")

    job = LegacyConfigAdapter.create_job(
        in_path=synthetic_video,
        out_path=out_path,
        filters=["Черно-белое"],
        zoom_p=100,
        speed_p=100,
        overlay_file=None,
        overlay_pos="Середина-Центр",
        output_format="Оригинальный",
        blur_background=False,
        mute_audio=False,
        strip_metadata=True,
        preset="ultrafast"
    )

    render_service = RenderService()
    render_service.render(job)

    assert os.path.exists(out_path)
    probe = FFprobeService()
    info = probe.inspect(out_path)

    assert info.has_video
    assert info.video.width == 640
    assert info.video.height == 360
