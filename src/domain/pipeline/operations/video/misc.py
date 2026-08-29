from dataclasses import dataclass
from src.domain.pipeline.graph.nodes import StreamRef
from src.domain.pipeline.graph.graph_context import GraphContext
from src.domain.pipeline.operations.base import VideoOperation


@dataclass(frozen=True)
class Zoom(VideoOperation):
    """
    Масштабирование (Zoom) видео с последующим кадрированием (если zoom > 1) или паддингом (если zoom < 1).
    """
    zoom_percent: int
    target_width: int = 0
    target_height: int = 0

    def apply(self, graph: GraphContext, video_in: StreamRef) -> StreamRef:
        factor = self.zoom_percent / 100.0
        if abs(factor - 1.0) < 1e-5:
            return video_in

        # 1. Scale
        scaled = graph.apply_filter("scale", [video_in], {
            "w": f"iw*{factor:.4f}",
            "h": f"ih*{factor:.4f}",
            "flags": "bicubic"
        })
        assert isinstance(scaled, StreamRef)

        # 2. Crop or Pad
        if self.target_width > 0 and self.target_height > 0:
            tw, th = self.target_width, self.target_height
            if factor > 1.0:
                res = graph.apply_filter("crop", [scaled], {
                    "w": tw,
                    "h": th,
                    "x": f"(in_w-{tw})/2",
                    "y": f"(in_h-{th})/2"
                })
            else:
                res = graph.apply_filter("pad", [scaled], {
                    "w": tw,
                    "h": th,
                    "x": f"(ow-iw)/2",
                    "y": f"(oh-ih)/2",
                    "color": "black"
                })
        else:
            if factor > 1.0:
                res = graph.apply_filter("crop", [scaled], {
                    "w": f"trunc(iw/{factor:.4f})",
                    "h": f"trunc(ih/{factor:.4f})"
                })
            else:
                res = graph.apply_filter("pad", [scaled], {
                    "w": f"trunc(iw/{factor:.4f})",
                    "h": f"trunc(ih/{factor:.4f})",
                    "x": "(ow-iw)/2",
                    "y": "(oh-ih)/2",
                    "color": "black"
                })
        assert isinstance(res, StreamRef)
        return res


@dataclass(frozen=True)
class VideoSpeed(VideoOperation):
    """Изменение скорости воспроизведения видео-потока (setpts)."""
    speed_factor: float

    def apply(self, graph: GraphContext, video_in: StreamRef) -> StreamRef:
        if abs(self.speed_factor - 1.0) < 1e-5:
            return video_in
        res = graph.apply_filter("setpts", [video_in], {"expr": f"PTS/{self.speed_factor:.4f}"})
        assert isinstance(res, StreamRef)
        return res


@dataclass(frozen=True)
class Overlay(VideoOperation):
    """Накладывает дополнительный поток поверх основного."""
    overlay_stream: StreamRef
    pos_expr: str = "x=(W-w)/2:y=(H-h)/2"
    shortest: bool = True

    def apply(self, graph: GraphContext, video_in: StreamRef) -> StreamRef:
        # Приведение оверлея к rgba для поддержки прозрачности
        ovl_alpha = graph.apply_filter("format", [self.overlay_stream], {"pix_fmts": "rgba"})
        assert isinstance(ovl_alpha, StreamRef)

        # Парсинг pos_expr "x=...:y=..." в словарь параметров
        params = {}
        for part in self.pos_expr.split(":"):
            if "=" in part:
                k, v = part.split("=", 1)
                params[k] = v
        if self.shortest:
            params["shortest"] = 1

        return graph.overlay(video_in, ovl_alpha, params=params)
