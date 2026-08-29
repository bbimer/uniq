import os
import threading
from typing import Optional, Callable
from src.domain.errors import RenderError, ErrorCode
from src.app.jobs.job import Job, JobStatus
from src.domain.pipeline.graph.validator import GraphValidator, GraphValidationError
from src.infrastructure.ffmpeg.graph_serializer import FFmpegGraphSerializer
from src.infrastructure.ffmpeg.command_builder import FFmpegCommandBuilder
from src.infrastructure.ffmpeg.encoder_resolver import EncoderResolver
from src.infrastructure.ffmpeg.probe_service import FFprobeService, ProbeError
from src.infrastructure.ffmpeg.runner import FFmpegRunner, FFmpegExecutionError
from src.infrastructure.ffmpeg.capabilities import CapabilityDetector


class RenderService:
    """
    Application-сервис для компиляции и исполнения одиночной задачи Job со структурированной обработкой ошибок.
    """

    def __init__(
        self,
        runner: Optional[FFmpegRunner] = None,
        probe_service: Optional[FFprobeService] = None,
        graph_validator: Optional[GraphValidator] = None,
        graph_serializer: Optional[FFmpegGraphSerializer] = None,
        encoder_resolver: Optional[EncoderResolver] = None,
        capability_detector: Optional[CapabilityDetector] = None
    ):
        self.runner = runner or FFmpegRunner()
        self.probe_service = probe_service or FFprobeService()
        self.validator = graph_validator or GraphValidator()
        self.serializer = graph_serializer or FFmpegGraphSerializer()
        self.encoder_resolver = encoder_resolver or EncoderResolver()
        self.capabilities = capability_detector or CapabilityDetector(self.runner.ffmpeg_bin)

    def render(
        self,
        job: Job,
        cancel_token: Optional[threading.Event] = None,
        on_progress: Optional[Callable[[float], None]] = None
    ) -> None:
        job.status = JobStatus.RUNNING
        job.progress = 0.0

        # Проверка существования входного файла
        if not os.path.exists(job.source_path):
            err = RenderError(
                code=ErrorCode.FILE_NOT_FOUND,
                message=f"Входной файл не существует: {job.source_path}",
                job_id=job.id
            )
            job.status = JobStatus.FAILED
            job.error_message = str(err)
            raise err

        try:
            # 1. Исследование исходного медиа-файла
            try:
                media_info = self.probe_service.inspect(job.source_path)
            except ProbeError as pe:
                raise RenderError(
                    code=ErrorCode.PROBE_FAILED,
                    message=f"Не удалось прочитать метаданные медиа-файла: {pe}",
                    job_id=job.id,
                    cause=pe
                )

            # 2. Построение графа операций
            graph = job.pipeline.build_graph(has_audio=media_info.has_audio)

            # 3. Валидация графа
            try:
                self.validator.validate(graph)
            except GraphValidationError as gve:
                raise RenderError(
                    code=ErrorCode.INVALID_GRAPH,
                    message=f"Граф операций некорректен: {gve}",
                    job_id=job.id,
                    cause=gve
                )

            # 4. Сериализация в filter_complex
            filter_complex, map_args = self.serializer.serialize(graph)

            # 5. Разрешение энкодера (с учетом доступных аппаратных кодеков)
            available_backends = list(self.capabilities.detect_backends())
            encoder_args = self.encoder_resolver.resolve(job.encoder, available_backends=available_backends)

            # 6. Сборка команды
            input_files = [job.source_path]
            if job.overlay_path and os.path.exists(job.overlay_path):
                input_files.append(job.overlay_path)

            is_gif_input = job.source_path.lower().endswith(".gif")

            cmd = FFmpegCommandBuilder.build(
                ffmpeg_bin=self.runner.ffmpeg_bin,
                input_files=input_files,
                filter_complex=filter_complex,
                map_args=map_args,
                encoder_args=encoder_args,
                output_path=job.target_path,
                is_gif_input=is_gif_input
            )

            # 7. Гарантируем существование директории вывода
            out_dir = os.path.dirname(os.path.abspath(job.target_path))
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)

            # 8. Запуск и исполнение
            def progress_bridge(p: float):
                job.progress = p
                if on_progress:
                    on_progress(p)

            try:
                self.runner.run(
                    cmd=cmd,
                    cancel_token=cancel_token,
                    on_progress=progress_bridge,
                    total_duration=media_info.duration
                )
            except InterruptedError:
                raise RenderError(
                    code=ErrorCode.CANCELLED,
                    message="Обработка была отменена пользователем",
                    job_id=job.id
                )
            except FFmpegExecutionError as fee:
                raise RenderError(
                    code=ErrorCode.FFMPEG_EXECUTION_FAILED,
                    message=f"Ошибка исполнения FFmpeg (код {fee.exit_code})",
                    job_id=job.id,
                    cause=fee,
                    details=fee.stderr_output
                )

            job.status = JobStatus.COMPLETED
            job.progress = 1.0

        except RenderError as re:
            job.status = JobStatus.CANCELLED if re.code == ErrorCode.CANCELLED else JobStatus.FAILED
            job.error_message = str(re)
            raise
        except Exception as ex:
            wrapped_err = RenderError(
                code=ErrorCode.UNKNOWN_ERROR,
                message=f"Непредвиденная ошибка: {ex}",
                job_id=job.id,
                cause=ex
            )
            job.status = JobStatus.FAILED
            job.error_message = str(wrapped_err)
            raise wrapped_err
