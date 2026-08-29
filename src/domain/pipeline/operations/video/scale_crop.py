from dataclasses import dataclass
from src.domain.pipeline.graph.nodes import StreamRef
from src.domain.pipeline.graph.graph_context import GraphContext
from src.domain.pipeline.operations.base import VideoOperation


@dataclass(frozen=True)
class Scale(VideoOperation):
    """Масштабирование видео с опциональным сохранением соотношения сторон."""
    width: int
    height: int
    force_original_aspect_ratio: str = "decrease"
    flags: str = "bicubic"

    def apply(self, graph: GraphContext, video_in: StreamRef) -> StreamRef:
        params = {
            "w": self.width,
            "h": self.height,
            "force_original_aspect_ratio": self.force_original_aspect_ratio,
            "flags": self.flags
        }
        res = graph.apply_filter("scale", [video_in], params=params)
        assert isinstance(res, StreamRef)
        return res


@dataclass(frozen=True)
class Pad(VideoOperation):
    """Добавление полей (letterbox/pillarbox)."""
    width: int
    height: int
    x: str = "(ow-iw)/2"
    y: str = "(oh-ih)/2"
    color: str = "black"

    def apply(self, graph: GraphContext, video_in: StreamRef) -> StreamRef:
        params = {
            "w": self.width,
            "h": self.height,
            "x": self.x,
            "y": self.y,
            "color": self.color
        }
        res = graph.apply_filter("pad", [video_in], params=params)
        assert isinstance(res, StreamRef)
        return res


@dataclass(frozen=True)
class Crop(VideoOperation):
    """Кадрирование видео."""
    width: int
    height: int
    x: str = "(in_w-out_w)/2"
    y: str = "(in_h-out_h)/2"

    def apply(self, graph: GraphContext, video_in: StreamRef) -> StreamRef:
        params = {
            "w": self.width,
            "h": self.height,
            "x": self.x,
            "y": self.y
        }
        res = graph.apply_filter("crop", [video_in], params=params)
        assert isinstance(res, StreamRef)
        return res
