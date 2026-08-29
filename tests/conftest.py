import os
import sys
import subprocess
import pytest

# Добавляем корень проекта в sys.path для импортов src.*
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture(scope="session")
def synthetic_video(tmp_path_factory):
    """Генерирует короткий тестовый видеофайл (2 сек, 640x360, 30fps с аудио) для тестов."""
    tmp_dir = tmp_path_factory.mktemp("media")
    video_path = os.path.join(tmp_dir, "test_input.mp4")
    
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "testsrc=duration=2:size=640x360:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        video_path
    ]
    subprocess.run(cmd, check=True)
    return video_path
