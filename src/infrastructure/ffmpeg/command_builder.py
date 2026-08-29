from typing import List, Sequence, Optional


class FFmpegCommandBuilder:
    """
    Формирует список аргументов командной строки для запуска процесса FFmpeg.
    """

    @staticmethod
    def build(
        ffmpeg_bin: str,
        input_files: Sequence[str],
        filter_complex: str,
        map_args: Sequence[str],
        encoder_args: Sequence[str],
        output_path: str,
        audio_codec_args: Optional[Sequence[str]] = None,
        shortest: bool = True,
        is_gif_input: bool = False
    ) -> List[str]:
        cmd: List[str] = [ffmpeg_bin, "-y", "-hide_banner", "-loglevel", "warning"]

        # Добавление входных файлов
        for idx, file_path in enumerate(input_files):
            if is_gif_input and idx == 0:
                cmd.extend(["-stream_loop", "-1", "-i", file_path])
            else:
                cmd.extend(["-i", file_path])

        # Добавление сложного графа фильтров
        if filter_complex:
            cmd.extend(["-filter_complex", filter_complex])

        # Добавление маппинга выходов
        cmd.extend(map_args)

        # Добавление параметров аудио-кодека
        if audio_codec_args:
            cmd.extend(audio_codec_args)
        else:
            # Если нет маппинга аудио, отключаем его
            has_audio_map = any("[aout]" in m or ":a" in m for m in map_args)
            if has_audio_map:
                cmd.extend(["-c:a", "aac", "-b:a", "192k"])
            else:
                cmd.append("-an")

        # Добавление параметров энкодера видео
        cmd.extend(encoder_args)

        if shortest and not is_gif_input:
            cmd.append("-shortest")

        cmd.append(output_path)
        return cmd
