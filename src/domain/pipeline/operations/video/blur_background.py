from dataclasses import dataclass
from src.domain.pipeline.graph.nodes import StreamRef
from src.domain.pipeline.graph.graph_context import GraphContext
from src.domain.pipeline.operations.base import VideoOperation


@dataclass(frozen=True)
class BlurBackground(VideoOperation):
    """
    Размытие фона для приведения к целевому формату (Reels 9:16).
    Разделяет поток, масштабирует и размывает фон, затем накладывает пропорционально масштабированный передний план.
    """
    target_width: int
    target_height: int
    blur_sigma: int = 25

    def apply(self, graph: GraphContext, video_in: StreamRef) -> StreamRef:
        fg_raw, bg_raw = graph.split(video_in, count=2)

        # 1. Задний фон: scale с увеличением -> crop -> gblur
        bg_scaled = graph.apply_filter("scale", [bg_raw], {
            "w": self.target_width,
            "h": self.target_height,
            "force_original_aspect_ratio": "increase"
        })
        bg_cropped = graph.apply_filter("crop", [bg_scaled], {
            "w": self.target_width,
            "h": self.target_height,
            "x": f"(in_w-{self.target_width})/2",
            "y": f"(in_h-{self.target_height})/2"
        })
        bg_blurred = graph.apply_filter("gblur", [bg_cropped], {"sigma": self.blur_sigma})

        # 2. Передний план: scale с уменьшением для сохранения пропорций
        fg_scaled = graph.apply_filter("scale", [fg_raw], {
            "w": self.target_width,
            "h": self.target_height,
            "force_original_aspect_ratio": "decrease"
        })

        # 3. Наложение переднего плана на размытый фон по центру
        return graph.overlay(bg_blurred, fg_scaled, {"x": "(W-w)/2", "y": "(H-h)/2", "shortest": 1})
