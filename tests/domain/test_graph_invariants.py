import pytest
from src.domain.media.media_info import MediaType
from src.domain.pipeline.graph.graph_context import GraphContext, GraphContextError
from src.domain.pipeline.graph.validator import GraphValidator, GraphValidationError
from src.domain.pipeline.graph.nodes import StreamRef


def test_empty_graph_raises_validation_error():
    graph = GraphContext()
    validator = GraphValidator()
    with pytest.raises(GraphValidationError) as exc:
        validator.validate(graph)
    assert "не содержит ни одного входного потока" in str(exc.value)


def test_missing_output_raises_validation_error():
    graph = GraphContext()
    v_in = graph.add_input(file_index=0, media_type=MediaType.VIDEO)
    _ = graph.apply_filter("scale", [v_in], {"w": 100, "h": 100})
    validator = GraphValidator()
    with pytest.raises(GraphValidationError) as exc:
        validator.validate(graph)
    assert "outputs пуст" in str(exc.value)


def test_audio_stream_passed_to_video_filter_raises_error():
    graph = GraphContext()
    a_in = graph.add_input(file_index=0, media_type=MediaType.AUDIO)
    # Попытка передать аудио в фильтр scale
    res = graph.apply_filter("scale", [a_in], {"w": 1080, "h": 1920})
    graph.set_output(res, label_hint="vout")

    validator = GraphValidator()
    with pytest.raises(GraphValidationError) as exc:
        validator.validate(graph)
    assert "Видео-фильтр 'scale' получил не-видео поток" in str(exc.value)


def test_video_stream_passed_to_audio_filter_raises_error():
    graph = GraphContext()
    v_in = graph.add_input(file_index=0, media_type=MediaType.VIDEO)
    # Попытка передать видео в фильтр atempo
    res = graph.apply_filter("atempo", [v_in], {"tempo": "1.2"})
    graph.set_output(res, label_hint="aout")

    validator = GraphValidator()
    with pytest.raises(GraphValidationError) as exc:
        validator.validate(graph)
    assert "Аудио-фильтр 'atempo' получил не-аудио поток" in str(exc.value)


def test_split_3_streams_and_consume_all():
    graph = GraphContext()
    v_in = graph.add_input(file_index=0, media_type=MediaType.VIDEO)
    s1, s2, s3 = graph.split(v_in, count=3)

    out1 = graph.apply_filter("scale", [s1], {"w": 100, "h": 100})
    out2 = graph.apply_filter("scale", [s2], {"w": 200, "h": 200})
    out3 = graph.apply_filter("scale", [s3], {"w": 300, "h": 300})

    # Объединяем два через overlay, а третий оставляем как второй выход
    ovl = graph.overlay(out1, out2)
    graph.set_output(ovl, label_hint="vout1")
    graph.set_output(out3, label_hint="vout2")

    validator = GraphValidator()
    validator.validate(graph)
    assert len(graph.outputs) == 2
