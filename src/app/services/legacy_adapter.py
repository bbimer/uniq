import os
import random
from typing import List, Optional
from src.domain.config.encoder_config import EncoderConfig, EncoderBackend
from src.domain.pipeline.pipeline import Pipeline
from src.domain.pipeline.operations.base import VideoOperation, AudioOperation
from src.domain.pipeline.operations.video.blur_background import BlurBackground
from src.domain.pipeline.operations.video.scale_crop import Scale, Pad
from src.domain.pipeline.operations.video.color_adjust import ColorAdjust, GenericFilter
from src.domain.pipeline.operations.video.misc import Zoom, VideoSpeed
from src.domain.pipeline.operations.audio.audio_ops import AudioSpeed
from src.app.jobs.job import Job


class LegacyConfigAdapter:
    """
    Адаптер для преобразования устаревших плоских параметров вызова process_single()
    в чистые доменные объекты Job, Pipeline и EncoderConfig.
    """

    REELS_WIDTH = 1080
    REELS_HEIGHT = 1920

    @classmethod
    def create_job(
        cls,
        in_path: str,
        out_path: str,
        filters: List[str],
        zoom_p: int,
        speed_p: int,
        overlay_file: Optional[str],
        overlay_pos: str,
        output_format: str,
        blur_background: bool,
        mute_audio: bool = False,
        strip_metadata: bool = True,
        hardware: str = "cpu",
        preset: str = "fast",
    ) -> Job:
        video_ops: List[VideoOperation] = []
        audio_ops: List[AudioOperation] = []

        is_reels_format = "1080x1920" in output_format or "Reels" in output_format

        # 1. Форматирование под целевой размер / размытие фона
        if is_reels_format:
            if blur_background:
                video_ops.append(BlurBackground(target_width=cls.REELS_WIDTH, target_height=cls.REELS_HEIGHT, blur_sigma=25))
            else:
                video_ops.append(Scale(width=cls.REELS_WIDTH, height=cls.REELS_HEIGHT, force_original_aspect_ratio="decrease"))
                video_ops.append(Pad(width=cls.REELS_WIDTH, height=cls.REELS_HEIGHT, x="(ow-iw)/2", y="(oh-ih)/2", color="black"))

        # 2. Цветовые фильтры
        for f_name in filters:
            if not f_name or f_name == "Нет фильтра":
                continue
            
            if f_name in ("Случайный фильтр", "Случ. цвет (яркость/контраст/...)"):
                br = random.uniform(-0.015, 0.015)
                ct = random.uniform(0.98, 1.02)
                sat = random.uniform(0.98, 1.02)
                hue = random.uniform(-0.5, 0.5)
                video_ops.append(ColorAdjust(brightness=br, contrast=ct, saturation=sat, hue=hue))
            elif f_name == "Черно-белое":
                video_ops.append(GenericFilter("hue", {"s": 0}))
            elif f_name == "Сепия":
                video_ops.append(GenericFilter("colorchannelmixer", {".393:.769:.189:0:.349:.686:.168:0:.272:.534:.131:0": True}))
            elif f_name == "Инверсия":
                video_ops.append(GenericFilter("negate"))
            elif f_name == "Размытие (легкое)":
                video_ops.append(GenericFilter("gblur", {"sigma": 2}))
            elif f_name == "Размытие (сильное)":
                video_ops.append(GenericFilter("gblur", {"sigma": 10}))
            elif f_name == "Отразить по горизонтали":
                video_ops.append(GenericFilter("hflip"))
            elif f_name == "Отразить по вертикали":
                video_ops.append(GenericFilter("vflip"))
            elif f_name == "Повыш. контрастность":
                video_ops.append(GenericFilter("eq", {"contrast": 1.5}))
            elif f_name == "Пониж. контрастность":
                video_ops.append(GenericFilter("eq", {"contrast": 0.7}))
            elif f_name == "Повыш. насыщенность":
                video_ops.append(GenericFilter("eq", {"saturation": 1.5}))
            elif f_name == "Пониж. насыщенность":
                video_ops.append(GenericFilter("eq", {"saturation": 0.5}))
            elif f_name == "Повыш. яркость":
                video_ops.append(GenericFilter("eq", {"brightness": 0.15}))
            elif f_name == "Пониж. яркость":
                video_ops.append(GenericFilter("eq", {"brightness": -0.15}))
            elif f_name == "Холодный фильтр":
                video_ops.append(GenericFilter("curves", {"b": "'0/0 0.4/0.5 1/1'", "g": "'0/0 0.4/0.4 1/1'"}))
            elif f_name == "Теплый фильтр":
                video_ops.append(GenericFilter("curves", {"r": "'0/0 0.4/0.5 1/1'", "g": "'0/0 0.6/0.6 1/1'"}))

        # 3. Zoom
        if zoom_p != 100:
            tw = cls.REELS_WIDTH if is_reels_format else 0
            th = cls.REELS_HEIGHT if is_reels_format else 0
            video_ops.append(Zoom(zoom_percent=zoom_p, target_width=tw, target_height=th))

        # 4. Скорость (видео и аудио)
        if speed_p != 100:
            speed_factor = speed_p / 100.0
            video_ops.append(VideoSpeed(speed_factor=speed_factor))
            audio_ops.append(AudioSpeed(speed_factor=speed_factor))

        # 5. Сборка Pipeline
        pipeline = Pipeline(
            video_operations=tuple(video_ops),
            audio_operations=tuple(audio_ops),
            mute_audio=mute_audio
        )

        # 6. Настройка энкодера
        backend = EncoderBackend.CPU
        if hardware.lower() == "nvidia":
            backend = EncoderBackend.NVIDIA
        elif hardware.lower() == "intel":
            backend = EncoderBackend.INTEL

        encoder_config = EncoderConfig(
            backend=backend,
            preset=preset,
            quality=19,
            strip_metadata=strip_metadata
        )

        return Job(
            id=os.path.basename(out_path),
            source_path=in_path,
            target_path=out_path,
            pipeline=pipeline,
            encoder=encoder_config,
            overlay_path=overlay_file
        )
