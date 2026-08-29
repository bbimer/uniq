import os
import shutil
import json
import subprocess
import platform
from typing import Optional
from src.domain.media.media_info import MediaInfo, VideoInfo, AudioInfo


class ProbeError(Exception):
    """Ошибка при исследовании медиа-файла через ffprobe."""
    pass


class FFprobeService:
    """
    Инфраструктурный сервис для получения метаданных медиа-файлов через ffprobe.
    """

    def __init__(self, ffprobe_path: Optional[str] = None):
        self._ffprobe_path = self._locate_ffprobe(ffprobe_path)

    @staticmethod
    def _locate_ffprobe(custom_path: Optional[str]) -> str:
        if custom_path and os.path.exists(custom_path):
            return custom_path
        in_path = shutil.which("ffprobe")
        if in_path:
            return in_path
        # Поиск рядом с проектом ffmpeg/bin/ffprobe.exe
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base_dir, "ffmpeg", "bin", "ffprobe.exe")
        if os.path.exists(local_bin):
            return local_bin
        return "ffprobe"

    def inspect(self, file_path: str) -> MediaInfo:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Медиа-файл не найден: {file_path}")

        cmd = [
            self._ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]

        creationflags = 0
        startupinfo = None
        if platform.system() == "Windows":
            creationflags = subprocess.CREATE_NO_WINDOW
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creationflags,
                startupinfo=startupinfo
            )
            data = json.loads(res.stdout)
        except Exception as e:
            raise ProbeError(f"Ошибка при вызове ffprobe для {os.path.basename(file_path)}: {e}")

        video_info: Optional[VideoInfo] = None
        audio_info: Optional[AudioInfo] = None

        format_info = data.get("format", {})
        total_duration = float(format_info.get("duration", 0.0) or 0.0)

        for stream in data.get("streams", []):
            codec_type = stream.get("codec_type")
            if codec_type == "video" and video_info is None:
                w = int(stream.get("width", 0) or 0)
                h = int(stream.get("height", 0) or 0)
                codec = stream.get("codec_name", "")
                pix_fmt = stream.get("pix_fmt", "yuv420p")
                
                # Парсинг fps
                r_frame_rate = stream.get("r_frame_rate", "30/1")
                fps = 30.0
                if "/" in r_frame_rate:
                    num, den = r_frame_rate.split("/")
                    if float(den) > 0:
                        fps = float(num) / float(den)

                dur = float(stream.get("duration", 0.0) or total_duration)
                video_info = VideoInfo(width=w, height=h, duration=dur, fps=fps, codec=codec, pixel_format=pix_fmt)

            elif codec_type == "audio" and audio_info is None:
                sample_rate = int(stream.get("sample_rate", 44100) or 44100)
                channels = int(stream.get("channels", 2) or 2)
                codec = stream.get("codec_name", "")
                bitrate = int(stream.get("bit_rate", 0) or 0)
                dur = float(stream.get("duration", 0.0) or total_duration)
                audio_info = AudioInfo(sample_rate=sample_rate, channels=channels, duration=dur, codec=codec, bitrate=bitrate)

        return MediaInfo(path=file_path, video=video_info, audio=audio_info)
