from src.domain.config.encoder_config import EncoderConfig, EncoderBackend
from src.infrastructure.ffmpeg.capabilities import CapabilityDetector
from src.infrastructure.ffmpeg.encoder_resolver import EncoderResolver


def test_capability_detector_always_includes_cpu():
    detector = CapabilityDetector()
    backends = detector.detect_backends()
    assert EncoderBackend.CPU in backends
    assert detector.is_backend_available(EncoderBackend.CPU) is True


def test_encoder_resolver_cpu():
    resolver = EncoderResolver()
    config = EncoderConfig(backend=EncoderBackend.CPU, preset="fast", quality=19, strip_metadata=True)
    args = resolver.resolve(config)

    assert "-c:v" in args
    assert "libx264" in args
    assert "-preset" in args
    assert "fast" in args
    assert "-crf" in args
    assert "19" in args
    assert "-map_metadata" in args


def test_encoder_resolver_fallback_to_cpu_when_unavailable():
    resolver = EncoderResolver()
    # Запрашиваем NVIDIA, но в списке доступных только CPU
    config = EncoderConfig(backend=EncoderBackend.NVIDIA, preset="fast", quality=19)
    args = resolver.resolve(config, available_backends=[EncoderBackend.CPU])

    # Должен автоматически переключиться на libx264
    assert "-c:v" in args
    assert "libx264" in args
