from src.domain.media.media_info import MediaType
from src.domain.pipeline.graph.graph_context import GraphContext
from src.domain.pipeline.operations.video.blur_background import BlurBackground
from src.domain.pipeline.operations.video.color_adjust import ColorAdjust
from src.domain.pipeline.operations.video.misc import Zoom, VideoSpeed
from src.domain.pipeline.operations.audio.audio_ops import AudioSpeed
from src.domain.pipeline.pipeline import Pipeline
from src.infrastructure.ffmpeg.graph_serializer import FFmpegGraphSerializer


def test_serialize_simple_pipeline():
    pipeline = Pipeline(
        video_operations=(
            ColorAdjust(brightness=0.015, contrast=1.02),
            Zoom(zoom_percent=104, target_width=1080, target_height=1920),
            VideoSpeed(speed_factor=1.02),
        ),
        audio_operations=(
            AudioSpeed(speed_factor=1.02),
        )
    )

    graph = pipeline.build_graph(has_audio=True)
    serializer = FFmpegGraphSerializer()
    fc_str, map_args = serializer.serialize(graph)

    # Проверяем структуру сгенерированного filter_complex
    assert "[0:v]" in fc_str
    assert "eq=brightness=0.0150:contrast=1.0200" in fc_str
    assert "scale=w=iw*1.0400:h=ih*1.0400:flags=bicubic" in fc_str
    assert "crop=w=1080:h=1920" in fc_str
    assert "setpts=PTS/1.0200" in fc_str
    assert "format=pix_fmts=yuv420p[vout]" in fc_str
    assert "[0:a]" in fc_str
    assert "atempo=tempo=1.0200" in fc_str
    assert "anull[aout]" in fc_str

    assert map_args == ["-map", "[vout]", "-map", "[aout]"]


def test_serialize_blur_background_reels():
    pipeline = Pipeline(
        video_operations=(
            BlurBackground(target_width=1080, target_height=1920, blur_sigma=25),
        )
    )

    graph = pipeline.build_graph(has_audio=False)
    serializer = FFmpegGraphSerializer()
    fc_str, map_args = serializer.serialize(graph)

    assert "split" in fc_str
    assert "scale=w=1080:h=1920:force_original_aspect_ratio=increase" in fc_str
    assert "crop=w=1080:h=1920" in fc_str
    assert "gblur=sigma=25" in fc_str
    assert "scale=w=1080:h=1920:force_original_aspect_ratio=decrease" in fc_str
    assert "overlay=" in fc_str
    assert "[vout]" in fc_str
    assert map_args == ["-map", "[vout]"]
