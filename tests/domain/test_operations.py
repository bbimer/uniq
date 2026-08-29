import pytest
from src.domain.media.media_info import MediaType
from src.domain.pipeline.graph.graph_context import GraphContext
from src.domain.pipeline.graph.validator import GraphValidator
from src.domain.pipeline.operations.video.scale_crop import Scale, Pad, Crop
from src.domain.pipeline.operations.video.blur_background import BlurBackground
from src.domain.pipeline.operations.video.color_adjust import ColorAdjust, GenericFilter
from src.domain.pipeline.operations.video.misc import Zoom, VideoSpeed
from src.domain.pipeline.operations.audio.audio_ops import AudioSpeed, AudioVolume


def test_scale_crop_pad_operations():
    graph = GraphContext()
    v_in = graph.add_input(file_index=0, media_type=MediaType.VIDEO)

    scale_op = Scale(width=1080, height=1920, force_original_aspect_ratio="decrease")
    v_scaled = scale_op.apply(graph, v_in)

    pad_op = Pad(width=1080, height=1920, x="(ow-iw)/2", y="(oh-ih)/2")
    v_padded = pad_op.apply(graph, v_scaled)

    crop_op = Crop(width=1000, height=1000)
    v_cropped = crop_op.apply(graph, v_padded)

    graph.set_output(v_cropped, label_hint="vout")
    GraphValidator().validate(graph)
    assert len(graph.nodes) == 3


def test_color_adjust_and_generic_filters():
    graph = GraphContext()
    v_in = graph.add_input(file_index=0, media_type=MediaType.VIDEO)

    color_op = ColorAdjust(brightness=0.02, contrast=1.05, saturation=1.1, hue=0.2)
    v_colored = color_op.apply(graph, v_in)

    hflip_op = GenericFilter("hflip")
    v_flipped = hflip_op.apply(graph, v_colored)

    graph.set_output(v_flipped, label_hint="vout")
    GraphValidator().validate(graph)
    # ColorAdjust produces 2 nodes (eq + hue) + hflip = 3 nodes
    assert len(graph.nodes) == 3


def test_zoom_in_and_out():
    # Zoom In (> 100%) -> scale + crop
    graph1 = GraphContext()
    v_in1 = graph1.add_input(file_index=0, media_type=MediaType.VIDEO)
    zoom_in = Zoom(zoom_percent=110, target_width=1080, target_height=1920)
    v_out1 = zoom_in.apply(graph1, v_in1)
    graph1.set_output(v_out1, label_hint="vout")
    GraphValidator().validate(graph1)
    assert len(graph1.nodes) == 2  # scale + crop

    # Zoom Out (< 100%) -> scale + pad
    graph2 = GraphContext()
    v_in2 = graph2.add_input(file_index=0, media_type=MediaType.VIDEO)
    zoom_out = Zoom(zoom_percent=90, target_width=1080, target_height=1920)
    v_out2 = zoom_out.apply(graph2, v_in2)
    graph2.set_output(v_out2, label_hint="vout")
    GraphValidator().validate(graph2)
    assert len(graph2.nodes) == 2  # scale + pad


def test_audio_speed_chaining():
    graph = GraphContext()
    a_in = graph.add_input(file_index=0, media_type=MediaType.AUDIO)

    # Скорость 3.0 должна разбиться на 2.0 и 1.5
    speed_op = AudioSpeed(speed_factor=3.0)
    a_out = speed_op.apply(graph, a_in)
    graph.set_output(a_out, label_hint="aout")
    GraphValidator().validate(graph)
    assert len(graph.nodes) == 2
    assert graph.nodes[0].params["tempo"] == "2.0"
    assert graph.nodes[1].params["tempo"] == "1.5000"
