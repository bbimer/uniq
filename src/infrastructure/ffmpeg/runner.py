import os
import shutil
import subprocess
import platform
import shlex
import threading
from typing import List, Optional, Callable


class FFmpegExecutionError(Exception):
    """Исключение при ошибке выполнения команды FFmpeg."""
    def __init__(self, exit_code: int, cmd: List[str], stderr_output: str):
        self.exit_code = exit_code
        self.cmd = cmd
        self.stderr_output = stderr_output
        cmd_str = " ".join(shlex.quote(str(c)) for c in cmd)
        super().__init__(
            f"FFmpeg завершился с кодом ошибки {exit_code}.\n"
            f"Команда: {cmd_str}\n"
            f"Вывод FFmpeg:\n{stderr_output}"
        )


class FFmpegRunner:
    """
    Инфраструктурный компонент для запуска и контроля процессов FFmpeg.
    Отвечает за потоки ввода-вывода, отмену задач и сбор ошибок.
    """

    def __init__(self, ffmpeg_bin: Optional[str] = None):
        self.ffmpeg_bin = self._locate_ffmpeg(ffmpeg_bin)

    @staticmethod
    def _locate_ffmpeg(custom_path: Optional[str]) -> str:
        if custom_path and os.path.exists(custom_path):
            return custom_path
        in_path = shutil.which("ffmpeg")
        if in_path:
            return in_path
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base_dir, "ffmpeg", "bin", "ffmpeg.exe")
        if os.path.exists(local_bin):
            return local_bin
        return "ffmpeg"

    def run(
        self,
        cmd: List[str],
        cancel_token: Optional[threading.Event] = None,
        on_progress: Optional[Callable[[float], None]] = None,
        total_duration: float = 0.0
    ) -> None:
        creationflags = 0
        startupinfo = None
        if platform.system() == "Windows":
            creationflags = subprocess.CREATE_NO_WINDOW
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creationflags,
            startupinfo=startupinfo
        )

        output_lines: List[str] = []

        try:
            while True:
                if cancel_token and cancel_token.is_set():
                    process.terminate()
                    try:
                        process.wait(timeout=2.0)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    raise InterruptedError("Выполнение FFmpeg было отменено пользователем.")

                line = process.stdout.readline()
                if not line:
                    break
                line_str = line.strip()
                if line_str:
                    output_lines.append(line_str)
                    
                    # Простой парсинг прогресса (time=00:00:05.12)
                    if on_progress and total_duration > 0 and "time=" in line_str:
                        try:
                            time_part = line_str.split("time=")[1].split()[0]
                            parts = time_part.split(":")
                            if len(parts) == 3:
                                current_sec = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                                progress = min(1.0, current_sec / total_duration)
                                on_progress(progress)
                        except Exception:
                            pass

            process.stdout.close()
            return_code = process.wait()

            if return_code != 0:
                recent_logs = "\n".join(output_lines[-20:])
                raise FFmpegExecutionError(return_code, cmd, recent_logs)

        except Exception:
            if process.poll() is None:
                process.kill()
            raise
