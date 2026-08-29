import pytest
from src.domain.config.encoder_config import EncoderConfig, EncoderBackend, EncoderPreference
from src.domain.errors import RenderError, ErrorCode
from src.infrastructure.ffmpeg.encoder_resolver import EncoderResolver


def test_encoder_required_raises_when_unavailable():
    resolver = EncoderResolver()
    # Запрашиваем NVIDIA с политикой REQUIRED, но доступен только CPU
    config = EncoderConfig(
        backend=EncoderBackend.NVIDIA,
        preference=EncoderPreference.REQUIRED
    )

    with pytest.raises(RenderError) as exc:
        resolver.resolve(config, available_backends=[EncoderBackend.CPU])

    assert exc.value.code == ErrorCode.ENCODER_UNAVAILABLE
    assert "недоступен" in exc.value.message


def test_encoder_preferred_falls_back_to_cpu():
    resolver = EncoderResolver()
    # Запрашиваем NVIDIA с политикой PREFERRED, доступен только CPU
    config = EncoderConfig(
        backend=EncoderBackend.NVIDIA,
        preference=EncoderPreference.PREFERRED
    )

    args = resolver.resolve(config, available_backends=[EncoderBackend.CPU])
    assert "-c:v" in args
    assert "libx264" in args


def test_encoder_auto_picks_best_available():
    resolver = EncoderResolver()
    config = EncoderConfig(backend=EncoderBackend.AUTO)

    # Если доступен NVIDIA -> выбирает h264_nvenc
    args_nv = resolver.resolve(config, available_backends=[EncoderBackend.CPU, EncoderBackend.NVIDIA])
    assert "h264_nvenc" in args_nv

    # Если доступен только CPU -> выбирает libx264
    args_cpu = resolver.resolve(config, available_backends=[EncoderBackend.CPU])
    assert "libx264" in args_cpu
