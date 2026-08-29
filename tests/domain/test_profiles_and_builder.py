from src.domain.config.profiles import REELS_TIKTOK_PROFILE, SHORTS_PROFILE, ORIGINAL_PROFILE
from src.domain.pipeline.builder import PipelineBuilder
from src.domain.pipeline.operations.video.blur_background import BlurBackground
from src.domain.pipeline.operations.video.scale_crop import Scale, Pad
from src.domain.pipeline.operations.video.color_adjust import ColorAdjust


def test_build_reels_profile():
    pipeline = PipelineBuilder.build_from_profile(REELS_TIKTOK_PROFILE, seed=42)
    # Первый элемент должен быть BlurBackground
    assert isinstance(pipeline.video_operations[0], BlurBackground)
    assert pipeline.video_operations[0].target_width == 1080
    assert pipeline.video_operations[0].target_height == 1920

    # Должен присутствовать ColorAdjust
    has_color = any(isinstance(op, ColorAdjust) for op in pipeline.video_operations)
    assert has_color is True


def test_build_shorts_profile_without_blur():
    pipeline = PipelineBuilder.build_from_profile(SHORTS_PROFILE, seed=42)
    # Shorts profile имеет blur_background=False -> Scale + Pad
    assert isinstance(pipeline.video_operations[0], Scale)
    assert isinstance(pipeline.video_operations[1], Pad)


def test_seed_determinism():
    """Тест на строгую воспроизводимость случайных параметров при одинаковом seed."""
    pipeline_1 = PipelineBuilder.build_from_profile(REELS_TIKTOK_PROFILE, seed=98765)
    pipeline_2 = PipelineBuilder.build_from_profile(REELS_TIKTOK_PROFILE, seed=98765)

    # Операции и их параметры должны быть абсолютно идентичны
    assert len(pipeline_1.video_operations) == len(pipeline_2.video_operations)
    for op1, op2 in zip(pipeline_1.video_operations, pipeline_2.video_operations):
        assert op1 == op2

    # При разном seed параметры будут отличаться
    pipeline_3 = PipelineBuilder.build_from_profile(REELS_TIKTOK_PROFILE, seed=11111)
    assert pipeline_1.video_operations != pipeline_3.video_operations
