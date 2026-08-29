from typing import Dict, List, Tuple
from src.domain.media.media_info import MediaType
from src.domain.pipeline.graph.nodes import StreamRef, FilterNode, GraphInput, GraphOutput
from src.domain.pipeline.graph.graph_context import GraphContext


class FFmpegGraphSerializer:
    """
    Детерминированный сериализатор Graph IR в синтаксис FFmpeg filter_complex.
    Не занимается валидацией (валидация выполняется отдельно через GraphValidator).
    """

    def serialize(self, context: GraphContext) -> Tuple[str, List[str]]:
        """
        Сериализует граф в:
        1. filter_complex строку
        2. список аргументов -map для выходов
        """
        stream_labels: Dict[StreamRef, str] = {}

        # 1. Присваиваем метки входным потокам файлов
        for g_inp in context.inputs:
            type_char = "v" if g_inp.media_type == MediaType.VIDEO else "a"
            stream_labels[g_inp.stream] = f"{g_inp.file_index}:{type_char}"

        # 2. Присваиваем метки промежуточным выходным потокам узлов
        # Выходные потоки, зарегистрированные в outputs, получат свои label_hint или vout/aout
        output_stream_map: Dict[StreamRef, str] = {}
        for g_out in context.outputs:
            if g_out.label_hint:
                output_stream_map[g_out.stream] = g_out.label_hint
            else:
                prefix = "vout" if g_out.media_type == MediaType.VIDEO else "aout"
                output_stream_map[g_out.stream] = prefix

        for node_idx, node in enumerate(context.nodes):
            for out_idx, out_s in enumerate(node.outputs):
                if out_s in output_stream_map:
                    stream_labels[out_s] = output_stream_map[out_s]
                else:
                    prefix = "v" if out_s.media_type == MediaType.VIDEO else "a"
                    stream_labels[out_s] = f"{prefix}_{out_s.id}"

        # 3. Формируем строковые описания каждого узла
        filter_strings: List[str] = []
        for node in context.nodes:
            in_str = "".join(f"[{stream_labels[s]}]" for s in node.inputs)
            out_str = "".join(f"[{stream_labels[s]}]" for s in node.outputs)
            
            param_parts: List[str] = []
            for k, v in node.params.items():
                if v is True:
                    param_parts.append(k)
                elif v is not None and v != "":
                    # Экранирование значений при необходимости
                    val_str = str(v)
                    if k == "expr":
                        # Для выражений типа setpts=PTS/1.02
                        param_parts.append(val_str)
                    elif k in ("w", "h", "x", "y", "flags", "force_original_aspect_ratio", "sigma", "color", "brightness", "contrast", "saturation", "tempo", "volume", "pix_fmts", "shortest", "outputs"):
                        param_parts.append(f"{k}={val_str}")
                    else:
                        param_parts.append(f"{k}={val_str}")

            params_str = ":".join(param_parts)
            if params_str:
                filter_strings.append(f"{in_str}{node.filter_name}={params_str}{out_str}")
            else:
                filter_strings.append(f"{in_str}{node.filter_name}{out_str}")

        filter_complex = ";".join(filter_strings)

        # 4. Формируем флаги -map для финальных выходов
        map_args: List[str] = []
        for g_out in context.outputs:
            label = stream_labels[g_out.stream]
            map_args.extend(["-map", f"[{label}]"])

        return filter_complex, map_args
