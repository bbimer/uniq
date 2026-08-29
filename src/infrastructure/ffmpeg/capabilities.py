import subprocess
import platform
from typing import List, Set, Optional
from src.domain.config.encoder_config import EncoderBackend


class CapabilityDetector:
    """
    Определяет доступность FFmpeg и аппаратных энкодеров (NVENC, QSV, AMF, VideoToolbox).
    """

    def __init__(self, ffmpeg_bin: str = "ffmpeg"):
        self.ffmpeg_bin = ffmpeg_bin
        self._cached_backends: Optional[Set[EncoderBackend]] = None

    def detect_backends(self, force_refresh: bool = False) -> Set[EncoderBackend]:
        if self._cached_backends is not None and not force_refresh:
            return set(self._cached_backends)

        available: Set[EncoderBackend] = {EncoderBackend.CPU}

        creationflags = 0
        startupinfo = None
        if platform.system() == "Windows":
            creationflags = subprocess.CREATE_NO_WINDOW
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        try:
            res = subprocess.run(
                [self.ffmpeg_bin, "-encoders", "-hide_banner"],
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
                errors="replace",
                creationflags=creationflags,
                startupinfo=startupinfo
            )
            stdout = res.stdout.lower()

            if "h264_nvenc" in stdout:
                available.add(EncoderBackend.NVIDIA)
            if "h264_qsv" in stdout:
                available.add(EncoderBackend.INTEL)
            if "h264_amf" in stdout:
                available.add(EncoderBackend.AMD)
            if "h264_videotoolbox" in stdout:
                available.add(EncoderBackend.APPLE)

        except Exception:
            pass

        self._cached_backends = available
        return set(available)

    def is_backend_available(self, backend: EncoderBackend) -> bool:
        if backend in (EncoderBackend.CPU, EncoderBackend.AUTO):
            return True
        available = self.detect_backends()
        return backend in available
