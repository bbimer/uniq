from dataclasses import dataclass, field
from typing import Sequence, Tuple, Optional
from src.domain.media.media_info import MediaType
from src.domain.pipeline.graph.nodes import StreamRef
from src.domain.pipeline.graph.graph_context import GraphContext
from src.domain.pipeline.operations.base import VideoOperation, AudioOperation


@dataclass(frozen=True)
class Pipeline:
    """
    Декларативное описание конвейера трансформаций медиа.
    """
    video_operations: Tuple[VideoOperation, ...] = field(default_factory=tuple)
    audio_operations: Tuple[AudioOperation, ...] = field(default_factory=tuple)
    mute_audio: bool = False

    def build_graph(self, has_audio: bool = True) -> GraphContext:
        """
        Строит полный GraphContext на основе списка зарегистрированных операций.
        """
        graph = GraphContext()

        # 1. Входной видео-поток (файл 0)
        v_curr = graph.add_input(file_index=0, media_type=MediaType.VIDEO)

        # 2. Применение видео-операций
        for v_op in self.video_operations:
            v_curr = v_op.apply(graph, v_curr)

        # 3. Финальный формат видео (yuv420p для совместимости с плеерами/соцсетями)
        v_final = graph.apply_filter("format", [v_curr], {"pix_fmts": "yuv420p"})
        assert isinstance(v_final, StreamRef)
        graph.set_output(v_final, label_hint="vout")

        # 4. Обработка аудио
        if has_audio and not self.mute_audio:
            a_curr = graph.add_input(file_index=0, media_type=MediaType.AUDIO)
            for a_op in self.audio_operations:
                a_curr = a_op.apply(graph, a_curr)
            a_final = graph.apply_filter("anull", [a_curr], {})
            assert isinstance(a_final, StreamRef)
            graph.set_output(a_final, label_hint="aout")

        return graph
