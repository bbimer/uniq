from dataclasses import dataclass
from typing import Tuple, Dict, Any, Union
from src.domain.media.media_info import MediaType


@dataclass(frozen=True)
class StreamRef:
    """Непрозрачный типизированный дескриптор потока данных в графе."""
    id: int
    media_type: MediaType

    def __repr__(self) -> str:
        return f"StreamRef({self.id}, {self.media_type.value})"


@dataclass(frozen=True)
class FilterNode:
    """Узел фильтрации в графе IR."""
    filter_name: str
    inputs: Tuple[StreamRef, ...]
    outputs: Tuple[StreamRef, ...]
    params: Dict[str, Any]

    def __repr__(self) -> str:
        in_str = ", ".join(repr(s) for s in self.inputs)
        out_str = ", ".join(repr(s) for s in self.outputs)
        return f"FilterNode({self.filter_name}, in=[{in_str}], out=[{out_str}], params={self.params})"


@dataclass(frozen=True)
class GraphInput:
    """Входной поток в граф из медиа-файла."""
    file_index: int
    media_type: MediaType
    stream: StreamRef


@dataclass(frozen=True)
class GraphOutput:
    """Выходной поток из графа."""
    media_type: MediaType
    stream: StreamRef
    label_hint: str = ""
