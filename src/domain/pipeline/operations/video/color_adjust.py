from dataclasses import dataclass
from typing import Dict, Any, Optional
from src.domain.pipeline.graph.nodes import StreamRef
from src.domain.pipeline.graph.graph_context import GraphContext
from src.domain.pipeline.operations.base import VideoOperation


@dataclass(frozen=True)
class ColorAdjust(VideoOperation):
    """Настройка яркости, контрастности, насыщенности и оттенка (eq + hue)."""
    brightness: float = 0.0
    contrast: float = 1.0
    saturation: float = 1.0
    hue: float = 0.0

    def apply(self, graph: GraphContext, video_in: StreamRef) -> StreamRef:
        current = video_in
        
        # eq filter
        eq_params = {}
        if abs(self.brightness) > 1e-5:
            eq_params["brightness"] = f"{self.brightness:.4f}"
        if abs(self.contrast - 1.0) > 1e-5:
            eq_params["contrast"] = f"{self.contrast:.4f}"
        if abs(self.saturation - 1.0) > 1e-5:
            eq_params["saturation"] = f"{self.saturation:.4f}"
        
        if eq_params:
            res = graph.apply_filter("eq", [current], params=eq_params)
            assert isinstance(res, StreamRef)
            current = res

        # hue filter
        if abs(self.hue) > 1e-5:
            res = graph.apply_filter("hue", [current], params={"h": f"{self.hue:.4f}"})
            assert isinstance(res, StreamRef)
            current = res

        return current


@dataclass(frozen=True)
class GenericFilter(VideoOperation):
    """Универсальная операция для стандартных видео-фильтров (hflip, vflip, negate, curves и т.д.)."""
    filter_name: str
    params: Optional[Dict[str, Any]] = None

    def apply(self, graph: GraphContext, video_in: StreamRef) -> StreamRef:
        res = graph.apply_filter(self.filter_name, [video_in], params=self.params or {})
        assert isinstance(res, StreamRef)
        return res
