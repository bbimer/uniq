import pytest
from src.domain.media.media_info import MediaType
from src.domain.pipeline.graph.graph_context import GraphContext, GraphContextError
from src.domain.pipeline.graph.validator import GraphValidator, GraphValidationError
from src.domain.pipeline.graph.nodes import StreamRef


def test_linear_graph_construction():
    graph = GraphContext()
    v_in = graph.add_input(file_index=0, media_type=MediaType.VIDEO)
    assert isinstance(v_in, StreamRef)
    assert v_in.media_type == MediaType.VIDEO

    v_scaled = graph.apply_filter("scale", [v_in], {"w": 1080, "h": 1920})
    assert isinstance(v_scaled, StreamRef)

    graph.set_output(v_scaled, label_hint="vout")

    # Валидация должна пройти успешно
    validator = GraphValidator()
    validator.validate(graph)

    assert len(graph.inputs) == 1
    assert len(graph.nodes) == 1
    assert len(graph.outputs) == 1


def test_dangling_stream_detected():
    graph = GraphContext()
    v_in = graph.add_input(file_index=0, media_type=MediaType.VIDEO)
    v_scaled = graph.apply_filter("scale", [v_in], {"w": 1080, "h": 1920})
    # Забыли вызвать graph.set_output()

    validator = GraphValidator()
    with pytest.raises(GraphValidationError) as exc:
        validator.validate(graph)
    assert "dangling streams" in str(exc.value)


def test_stream_reuse_without_split_raises_error():
    graph = GraphContext()
    v_in = graph.add_input(file_index=0, media_type=MediaType.VIDEO)
    
    # Первое использование
    _ = graph.apply_filter("scale", [v_in], {"w": 1080, "h": 1920})

    # Попытка повторно использовать v_in без split
    with pytest.raises(GraphContextError) as exc:
        _ = graph.apply_filter("crop", [v_in], {"w": 500, "h": 500})
    assert "уже был использован" in str(exc.value)


def test_split_and_overlay_graph():
    graph = GraphContext()
    v_in = graph.add_input(file_index=0, media_type=MediaType.VIDEO)

    fg, bg = graph.split(v_in, count=2)
    assert fg != bg

    bg_scaled = graph.apply_filter("scale", [bg], {"w": 1080, "h": 1920})
    bg_blurred = graph.apply_filter("gblur", [bg_scaled], {"sigma": 25})

    fg_scaled = graph.apply_filter("scale", [fg], {"w": 1080, "h": 1920})

    result = graph.overlay(bg_blurred, fg_scaled, {"x": 0, "y": 0})
    graph.set_output(result, label_hint="vout")

    validator = GraphValidator()
    validator.validate(graph)
    assert len(graph.nodes) == 5
