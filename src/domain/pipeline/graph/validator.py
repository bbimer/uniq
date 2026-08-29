from typing import List, Set, Dict
from src.domain.media.media_info import MediaType
from src.domain.pipeline.graph.nodes import StreamRef, FilterNode, GraphInput, GraphOutput
from src.domain.pipeline.graph.graph_context import GraphContext


class GraphValidationError(Exception):
    """Ошибка валидации графа перед сериализацией/исполнением."""
    def __init__(self, errors: List[str]):
        self.errors = errors
        msg = "Ошибки валидации графа:\n - " + "\n - ".join(errors)
        super().__init__(msg)


class GraphValidator:
    """
    Проверяет целостность, связность и ацикличность графа перед передачей в сериализатор.
    """

    KNOWN_AUDIO_ONLY_FILTERS = {"anull", "atempo", "volume", "equalizer", "highpass", "lowpass", "asplit", "amix", "aresample", "asetrate"}
    KNOWN_VIDEO_ONLY_FILTERS = {"scale", "crop", "pad", "gblur", "eq", "hue", "format", "split", "overlay", "setpts", "rotate", "hflip", "vflip", "noise", "curves"}

    def validate(self, context: GraphContext) -> None:
        errors: List[str] = []

        if not context.inputs:
            errors.append("Граф не содержит ни одного входного потока (inputs пуст).")

        if not context.outputs:
            errors.append("Граф не содержит ни одного выходного потока (outputs пуст).")

        # 1. Проверка наличия 'dangling' (зависших) потоков
        all_created: Set[StreamRef] = set(context._active_streams)
        all_consumed: Set[StreamRef] = set(context._consumed_streams)
        unconsumed = all_created - all_consumed
        if unconsumed:
            errors.append(f"Обнаружены неиспользованные потоки (dangling streams): {unconsumed}")

        # 2. Проверка типов медиа для известных фильтров
        for node in context.nodes:
            if node.filter_name in self.KNOWN_AUDIO_ONLY_FILTERS:
                for inp in node.inputs:
                    if inp.media_type != MediaType.AUDIO:
                        errors.append(f"Аудио-фильтр '{node.filter_name}' получил не-аудио поток {inp}.")
            elif node.filter_name in self.KNOWN_VIDEO_ONLY_FILTERS:
                for inp in node.inputs:
                    if inp.media_type != MediaType.VIDEO:
                        errors.append(f"Видео-фильтр '{node.filter_name}' получил не-видео поток {inp}.")

        # 3. Проверка на ацикличность (DAG)
        # Каждое ребро идет от node_source (производитель потока) к node_target (потребитель)
        producer_map: Dict[StreamRef, int] = {}
        for inp_idx, g_inp in enumerate(context.inputs):
            producer_map[g_inp.stream] = -1 - inp_idx  # виртуальный узел входа

        for node_idx, node in enumerate(context.nodes):
            for out_s in node.outputs:
                producer_map[out_s] = node_idx

        adj_list: Dict[int, List[int]] = {i: [] for i in range(len(context.nodes))}
        in_degree: Dict[int, int] = {i: 0 for i in range(len(context.nodes))}

        for node_idx, node in enumerate(context.nodes):
            for in_s in node.inputs:
                prod_node = producer_map.get(in_s)
                if prod_node is not None and prod_node >= 0:
                    adj_list[prod_node].append(node_idx)
                    in_degree[node_idx] += 1

        # Топологическая сортировка (алгоритм Кана)
        queue = [i for i in range(len(context.nodes)) if in_degree[i] == 0]
        visited_count = 0
        while queue:
            curr = queue.pop(0)
            visited_count += 1
            for neighbor in adj_list[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count < len(context.nodes):
            errors.append("В графе обнаружены циклы (граф не является ациклическим DAG).")

        if errors:
            raise GraphValidationError(errors)
