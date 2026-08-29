import random
from typing import List, Optional
from src.domain.config.profiles import Profile, TargetAspectRatio
from src.domain.pipeline.pipeline import Pipeline
from src.domain.pipeline.operations.base import VideoOperation, AudioOperation
from src.domain.pipeline.operations.video.scale_crop import Scale, Pad
from src.domain.pipeline.operations.video.blur_background import BlurBackground
from src.domain.pipeline.operations.video.color_adjust import ColorAdjust, GenericFilter
from src.domain.pipeline.operations.video.misc import Zoom, VideoSpeed
from src.domain.pipeline.operations.audio.audio_ops import AudioSpeed


class PipelineBuilder:
    """
    Фабрика для детерминированного построения Pipeline из декларативного Profile и seed.
    """

    @staticmethod
    def build_from_profile(profile: Profile, seed: Optional[int] = None) -> Pipeline:
        rng = random.Random(seed)
        video_ops: List[VideoOperation] = []
        audio_ops: List[AudioOperation] = []

        # 1. Форматирование кадра и фон
        if profile.target_ratio != TargetAspectRatio.ORIGINAL and profile.target_width > 0 and profile.target_height > 0:
            tw, th = profile.target_width, profile.target_height
            if profile.blur_background:
                video_ops.append(BlurBackground(target_width=tw, target_height=th, blur_sigma=25))
            else:
                video_ops.append(Scale(width=tw, height=th, force_original_aspect_ratio="decrease"))
                video_ops.append(Pad(width=tw, height=th, x="(ow-iw)/2", y="(oh-ih)/2", color="black"))

        # 2. Цветовые фильтры
        if profile.color_jitter.enabled:
            cj = profile.color_jitter
            br = rng.uniform(cj.brightness_range[0], cj.brightness_range[1])
            ct = rng.uniform(cj.contrast_range[0], cj.contrast_range[1])
            sat = rng.uniform(cj.saturation_range[0], cj.saturation_range[1])
            hue = rng.uniform(cj.hue_range[0], cj.hue_range[1])
            video_ops.append(ColorAdjust(brightness=br, contrast=ct, saturation=sat, hue=hue))

        for f_name in profile.filter_names:
            if f_name == "Черно-белое":
                video_ops.append(GenericFilter("hue", {"s": 0}))
            elif f_name == "Инверсия":
                video_ops.append(GenericFilter("negate"))
            elif f_name == "Отразить по горизонтали":
                video_ops.append(GenericFilter("hflip"))
            elif f_name == "Отразить по вертикали":
                video_ops.append(GenericFilter("vflip"))

        # 3. Zoom
        if profile.zoom.enabled:
            zoom_val = rng.randint(profile.zoom.min_percent, profile.zoom.max_percent)
            if zoom_val != 100:
                tw = profile.target_width if profile.target_ratio != TargetAspectRatio.ORIGINAL else 0
                th = profile.target_height if profile.target_ratio != TargetAspectRatio.ORIGINAL else 0
                video_ops.append(Zoom(zoom_percent=zoom_val, target_width=tw, target_height=th))

        # 4. Скорость
        if profile.speed.enabled:
            speed_val = rng.randint(profile.speed.min_percent, profile.speed.max_percent)
            if speed_val != 100:
                speed_factor = speed_val / 100.0
                video_ops.append(VideoSpeed(speed_factor=speed_factor))
                audio_ops.append(AudioSpeed(speed_factor=speed_factor))

        return Pipeline(
            video_operations=tuple(video_ops),
            audio_operations=tuple(audio_ops),
            mute_audio=profile.mute_audio
        )
