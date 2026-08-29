import subprocess
import threading
import time
import pytest
from src.infrastructure.ffmpeg.runner import FFmpegRunner, FFmpegExecutionError


def test_runner_success():
    runner = FFmpegRunner()
    cmd = [
        runner.ffmpeg_bin, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "nullsrc=duration=0.1:size=100x100:rate=10",
        "-f", "null", "-"
    ]
    runner.run(cmd)


def test_runner_non_zero_exit_raises_exception():
    runner = FFmpegRunner()
    cmd = [
        runner.ffmpeg_bin, "-y", "-hide_banner",
        "-f", "lavfi", "-i", "nullsrc=duration=0.1",
        "-vf", "non_existent_filter_xyz_123",
        "-f", "null", "-"
    ]
    with pytest.raises(FFmpegExecutionError) as exc:
        runner.run(cmd)
    assert exc.value.exit_code != 0
    assert "non_existent_filter_xyz_123" in exc.value.stderr_output or "No such filter" in exc.value.stderr_output


def test_runner_cancellation_pre_set():
    """Тест отмены до/в момент старта."""
    runner = FFmpegRunner()
    cancel_token = threading.Event()
    cancel_token.set()

    cmd = [
        runner.ffmpeg_bin, "-y", "-hide_banner",
        "-f", "lavfi", "-i", "testsrc=duration=10:size=320x240:rate=30",
        "-f", "null", "-"
    ]

    with pytest.raises(InterruptedError):
        runner.run(cmd, cancel_token=cancel_token)


def test_runner_cancellation_during_execution():
    """Тест отмены в процессе длительного выполнения."""
    runner = FFmpegRunner()
    cancel_token = threading.Event()

    # Генерация 60 секунд синтетического видео (медленная)
    cmd = [
        runner.ffmpeg_bin, "-y", "-hide_banner",
        "-f", "lavfi", "-i", "testsrc=duration=60:size=1920x1080:rate=60",
        "-c:v", "libx264", "-preset", "veryslow",
        "-f", "null", "-"
    ]

    def _cancel_delayed():
        time.sleep(0.1)
        cancel_token.set()

    thread = threading.Thread(target=_cancel_delayed)
    thread.start()

    with pytest.raises(InterruptedError):
        runner.run(cmd, cancel_token=cancel_token)

    thread.join()
