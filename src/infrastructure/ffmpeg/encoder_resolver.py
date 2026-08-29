from typing import List, Optional
from src.domain.config.encoder_config import EncoderConfig, EncoderBackend, EncoderPreference
from src.domain.errors import RenderError, ErrorCode


class EncoderResolver:
    """
    Преобразует доменный EncoderConfig в аргументы кодирования FFmpeg с учетом политики EncoderPreference.
    """

    NVENC_PRESETS = {
        "ultrafast": "p1", "superfast": "p2", "veryfast": "p3", "faster": "p4",
        "fast": "p4", "medium": "p5", "slow": "p6", "slower": "p7", "veryslow": "p7",
    }

    QSV_PRESETS = {
        "ultrafast": "veryfast", "superfast": "faster", "veryfast": "fast",
        "fast": "medium", "medium": "medium", "slow": "slow", "veryslow": "veryslow",
    }

    def resolve(self, config: EncoderConfig, available_backends: Optional[List[EncoderBackend]] = None) -> List[str]:
        target_backend = config.backend
        avail = available_backends if available_backends is not None else [EncoderBackend.CPU]

        # 1. Автоматический выбор лучшего доступного энкодера
        if target_backend == EncoderBackend.AUTO:
            if EncoderBackend.NVIDIA in avail:
                target_backend = EncoderBackend.NVIDIA
            elif EncoderBackend.INTEL in avail:
                target_backend = EncoderBackend.INTEL
            elif EncoderBackend.AMD in avail:
                target_backend = EncoderBackend.AMD
            elif EncoderBackend.APPLE in avail:
                target_backend = EncoderBackend.APPLE
            else:
                target_backend = EncoderBackend.CPU

        # 2. Обработка явно указанного бэкенда
        elif target_backend not in avail and target_backend != EncoderBackend.CPU:
            if config.preference == EncoderPreference.REQUIRED:
                raise RenderError(
                    code=ErrorCode.ENCODER_UNAVAILABLE,
                    message=f"Требуемый аппаратный энкодер '{target_backend.value}' недоступен в FFmpeg на данной системе."
                )
            else:
                # Fallback на CPU при PREFERRED
                target_backend = EncoderBackend.CPU

        # 3. Формирование аргументов кодирования
        args: List[str] = []

        if target_backend == EncoderBackend.NVIDIA:
            args.extend(["-c:v", "h264_nvenc"])
            nv_preset = self.NVENC_PRESETS.get(config.preset, "p4")
            args.extend(["-preset", nv_preset])
            if config.quality is not None:
                args.extend(["-cq", str(config.quality)])
            if config.bitrate_kbps:
                args.extend(["-b:v", f"{config.bitrate_kbps}k"])

        elif target_backend == EncoderBackend.INTEL:
            args.extend(["-c:v", "h264_qsv"])
            qsv_preset = self.QSV_PRESETS.get(config.preset, "medium")
            args.extend(["-preset", qsv_preset])
            if config.quality is not None:
                args.extend(["-global_quality", str(config.quality)])

        elif target_backend == EncoderBackend.AMD:
            args.extend(["-c:v", "h264_amf"])
            if config.quality is not None:
                args.extend(["-qp_i", str(config.quality), "-qp_p", str(config.quality)])

        elif target_backend == EncoderBackend.APPLE:
            args.extend(["-c:v", "h264_videotoolbox"])
            if config.quality is not None:
                args.extend(["-q:v", str(max(1, min(100, 100 - config.quality * 2)))])

        else:  # CPU (libx264)
            args.extend(["-c:v", "libx264"])
            args.extend(["-preset", config.preset])
            if config.quality is not None:
                args.extend(["-crf", str(config.quality)])
            if config.bitrate_kbps:
                args.extend(["-b:v", f"{config.bitrate_kbps}k"])

        if config.strip_metadata:
            args.extend(["-map_metadata", "-1", "-map_chapters", "-1"])

        return args
