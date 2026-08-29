from src.domain.pipeline.pipeline import Pipeline
from src.domain.pipeline.operations.video.scale_crop import Scale, Pad, Crop
from src.domain.pipeline.operations.video.blur_background import BlurBackground
from src.domain.pipeline.operations.video.color_adjust import ColorAdjust, GenericFilter
from src.domain.pipeline.operations.video.misc import Zoom, VideoSpeed
from src.domain.pipeline.operations.audio.audio_ops import AudioSpeed, AudioVolume
from src.infrastructure.ffmpeg.graph_serializer import FFmpegGraphSerializer


def test_golden_reels_pipeline():
    """Эталонный тест сериализации графа для Reels (BlurBackground + Color + Zoom + Speed + Audio)."""
    pipeline = Pipeline(
        video_operations=(
            BlurBackground(target_width=1080, target_height=1920, blur_sigma=25),
            ColorAdjust(brightness=0.010, contrast=1.020, saturation=1.050),
            Zoom(zoom_percent=103, target_width=1080, target_height=1920),
            VideoSpeed(speed_factor=1.02),
        ),
        audio_operations=(
            AudioSpeed(speed_factor=1.02),
            AudioVolume(volume=0.95),
        )
    )

    graph = pipeline.build_graph(has_audio=True)
    fc_str, map_args = FFmpegGraphSerializer().serialize(graph)

    # Проверяем ключевые фрагменты графа
    expected_fragments = [
        "[0:v]split[v_2][v_3]",
        "[v_3]scale=w=1080:h=1920:force_original_aspect_ratio=increase[v_4]",
        "[v_4]crop=w=1080:h=1920:x=(in_w-1080)/2:y=(in_h-1920)/2[v_5]",
        "[v_5]gblur=sigma=25[v_6]",
        "[v_2]scale=w=1080:h=1920:force_original_aspect_ratio=decrease[v_7]",
        "[v_6][v_7]overlay=x=(W-w)/2:y=(H-h)/2:shortest=1[v_8]",
        "[v_8]eq=brightness=0.0100:contrast=1.0200:saturation=1.0500[v_9]",
        "[v_9]scale=w=iw*1.0300:h=ih*1.0300:flags=bicubic[v_10]",
        "[v_10]crop=w=1080:h=1920:x=(in_w-1080)/2:y=(in_h-1920)/2[v_11]",
        "[v_11]setpts=PTS/1.0200[v_12]",
        "[v_12]format=pix_fmts=yuv420p[vout]",
        "[0:a]atempo=tempo=1.0200[a_15]",
        "[a_15]volume=volume=0.950[a_16]",
        "[a_16]anull[aout]",
    ]

    for frag in expected_fragments:
        assert frag in fc_str, f"Фрагмент '{frag}' не найден в сериализованном графе:\n{fc_str}"

    assert map_args == ["-map", "[vout]", "-map", "[aout]"]


def test_golden_muted_pipeline():
    """Тест сериализации, когда аудио отключено (mute_audio=True)."""
    pipeline = Pipeline(
        video_operations=(
            GenericFilter("hflip"),
        ),
        mute_audio=True
    )

    graph = pipeline.build_graph(has_audio=True)
    fc_str, map_args = FFmpegGraphSerializer().serialize(graph)

    assert "[0:v]hflip[v_2]" in fc_str
    assert "[v_2]format=pix_fmts=yuv420p[vout]" in fc_str
    assert "[0:a]" not in fc_str
    assert map_args == ["-map", "[vout]"]
