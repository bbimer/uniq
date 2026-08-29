from dataclasses import dataclass
from src.domain.pipeline.graph.nodes import StreamRef
from src.domain.pipeline.graph.graph_context import GraphContext
from src.domain.pipeline.operations.base import AudioOperation


@dataclass(frozen=True)
class AudioSpeed(AudioOperation):
    """
    Изменение скорости воспроизведения аудио (atempo).
    FFmpeg atempo поддерживает значения только от 0.5 до 2.0, поэтому для больших изменений строится цепочка.
    """
    speed_factor: float

    def apply(self, graph: GraphContext, audio_in: StreamRef) -> StreamRef:
        if abs(self.speed_factor - 1.0) < 1e-5:
            return audio_in

        current = audio_in
        cur = self.speed_factor

        # Если скорость > 2.0, разбиваем на умножения по 2.0
        while cur > 2.0:
            res = graph.apply_filter("atempo", [current], {"tempo": "2.0"})
            assert isinstance(res, StreamRef)
            current = res
            cur /= 2.0

        # Если скорость < 0.5, разбиваем на деления по 0.5
        min_tempo = 0.5
        while cur < min_tempo:
            res = graph.apply_filter("atempo", [current], {"tempo": f"{min_tempo:.2f}"})
            assert isinstance(res, StreamRef)
            current = res
            cur /= min_tempo

        # Оставшаяся часть
        if abs(cur - 1.0) > 1e-5 and min_tempo <= cur <= 2.0:
            res = graph.apply_filter("atempo", [current], {"tempo": f"{cur:.4f}"})
            assert isinstance(res, StreamRef)
            current = res

        return current


@dataclass(frozen=True)
class AudioVolume(AudioOperation):
    """Изменение громкости аудио."""
    volume: float

    def apply(self, graph: GraphContext, audio_in: StreamRef) -> StreamRef:
        if abs(self.volume - 1.0) < 1e-5:
            return audio_in
        res = graph.apply_filter("volume", [audio_in], {"volume": f"{self.volume:.3f}"})
        assert isinstance(res, StreamRef)
        return res
