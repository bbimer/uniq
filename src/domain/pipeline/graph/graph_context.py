from typing import List, Dict, Any, Optional, Sequence, Union, Tuple, Set
from src.domain.media.media_info import MediaType
from src.domain.pipeline.graph.nodes import StreamRef, FilterNode, GraphInput, GraphOutput


class GraphContextError(Exception):
    """Ошибка при построении графа обработки медиа."""
    pass


class GraphContext:
    """
    Единственный владелец и строитель графа операций (Graph IR).
    Управляет созданием узлов, дескрипторами потоков StreamRef и их жизненным циклом.
    """

    def __init__(self):
        self._next_stream_id: int = 0
        self._inputs: List[GraphInput] = []
        self._nodes: List[FilterNode] = []
        self._outputs: List[GraphOutput] = []
        self._consumed_streams: Set[StreamRef] = set()
        self._active_streams: Set[StreamRef] = set()

    def _create_stream(self, media_type: MediaType) -> StreamRef:
        self._next_stream_id += 1
        stream = StreamRef(id=self._next_stream_id, media_type=media_type)
        self._active_streams.add(stream)
        return stream

    def add_input(self, file_index: int, media_type: MediaType) -> StreamRef:
        """Регистрирует входной поток из файла с индексом file_index."""
        stream = self._create_stream(media_type)
        self._inputs.append(GraphInput(file_index=file_index, media_type=media_type, stream=stream))
        return stream

    def apply_filter(
        self,
        filter_name: str,
        inputs: Sequence[StreamRef],
        params: Optional[Dict[str, Any]] = None,
        output_type: Optional[MediaType] = None,
        num_outputs: int = 1
    ) -> Union[StreamRef, Tuple[StreamRef, ...]]:
        """
        Применяет фильтр к входным потокам и возвращает один или несколько выходных потоков.
        """
        if not inputs:
            raise GraphContextError(f"Фильтр '{filter_name}' должен иметь хотя бы один входной поток.")
        
        # Проверка, что все входные потоки существуют и активны
        for s in inputs:
            if s not in self._active_streams:
                raise GraphContextError(f"Поток {s} не существует в текущем контексте графа.")
            if s in self._consumed_streams:
                raise GraphContextError(
                    f"Поток {s} уже был использован в другом фильтре. "
                    "Для повторного использования используйте graph.split()."
                )

        # Помечаем входные потоки как использованные
        for s in inputs:
            self._consumed_streams.add(s)

        # Определение типа выходных потоков
        if output_type is None:
            output_type = inputs[0].media_type

        # Создание выходных потоков
        out_streams: List[StreamRef] = []
        for _ in range(num_outputs):
            out_streams.append(self._create_stream(output_type))

        node = FilterNode(
            filter_name=filter_name,
            inputs=tuple(inputs),
            outputs=tuple(out_streams),
            params=dict(params or {})
        )
        self._nodes.append(node)

        if num_outputs == 1:
            return out_streams[0]
        return tuple(out_streams)

    def split(self, source: StreamRef, count: int = 2) -> Tuple[StreamRef, ...]:
        """
        Разделяет один поток на несколько независимых копий (split / asplit).
        """
        if count < 2:
            raise GraphContextError("Количество потоков при split должно быть >= 2.")
        
        filter_name = "split" if source.media_type == MediaType.VIDEO else "asplit"
        params = {} if count == 2 else {"outputs": count}
        
        res = self.apply_filter(
            filter_name=filter_name,
            inputs=[source],
            params=params,
            output_type=source.media_type,
            num_outputs=count
        )
        return res if isinstance(res, tuple) else (res,)

    def overlay(
        self,
        main: StreamRef,
        overlay_stream: StreamRef,
        params: Optional[Dict[str, Any]] = None
    ) -> StreamRef:
        """
        Накладывает overlay_stream поверх main потока.
        """
        if main.media_type != MediaType.VIDEO or overlay_stream.media_type != MediaType.VIDEO:
            raise GraphContextError("Оба входа для overlay должны быть видео-потоками (MediaType.VIDEO).")

        res = self.apply_filter(
            filter_name="overlay",
            inputs=[main, overlay_stream],
            params=params or {},
            output_type=MediaType.VIDEO,
            num_outputs=1
        )
        assert isinstance(res, StreamRef)
        return res

    def set_output(self, stream: StreamRef, label_hint: str = "") -> None:
        """Регистрирует поток как финальный выходной поток графа."""
        if stream not in self._active_streams:
            raise GraphContextError(f"Поток {stream} не существует в текущем контексте графа.")
        if stream in self._consumed_streams:
            raise GraphContextError(f"Поток {stream} уже был потреблен фильтром и не может быть выходом.")
        
        self._consumed_streams.add(stream)
        self._outputs.append(GraphOutput(media_type=stream.media_type, stream=stream, label_hint=label_hint))

    @property
    def inputs(self) -> List[GraphInput]:
        return list(self._inputs)

    @property
    def nodes(self) -> List[FilterNode]:
        return list(self._nodes)

    @property
    def outputs(self) -> List[GraphOutput]:
        return list(self._outputs)
