# batch_x12.py — Пакетная уникализация под 12 аккаунтов по 6 роликов на каждый (72 ролика)
import os
import sys
import random
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.ffmpeg_utils import process_single
from utils.constants import (
    VALID_INPUT_EXTENSIONS, REELS_FORMAT_NAME,
    DEFAULT_OUTPUT_DIR
)

# ─── НАСТРОЙКИ BATCH X12 ─────────────────────────────────────
NUM_ACCOUNTS = 12                     # Количество аккаунтов
VIDEOS_PER_ACCOUNT = 6                # Количество роликов на каждый аккаунт

INPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input")
OUTPUT_DIR = DEFAULT_OUTPUT_DIR

ZOOM_MIN = 100                        # Мин. zoom % (100–104% незаметно для глаза)
ZOOM_MAX = 104                        # Макс. zoom %
SPEED_MIN = 98                        # Мин. скорость % (98–102% с сохранением питча)
SPEED_MAX = 102                       # Макс. скорость %

OUTPUT_FORMAT = REELS_FORMAT_NAME     # TikTok/Reels 1080x1920
BLUR_BACKGROUND = True                # Размытый фон, если видео горизонтальное
MUTE_AUDIO = False
STRIP_METADATA = True

# Пул фильтров (микро-цветокоррекция)
RANDOM_FILTER_POOL = [
    "Случ. цвет (яркость/контраст/...)",
]
# ─────────────────────────────────────────────────────────────


def find_videos(directory: str) -> list:
    """Ищет все видеофайлы в папке input."""
    videos = []
    if not os.path.isdir(directory):
        return videos
    for f in os.listdir(directory):
        ext = os.path.splitext(f)[1].lower()
        if ext in VALID_INPUT_EXTENSIONS:
            videos.append(os.path.join(directory, f))
    return sorted(videos)


def check_gpu_available() -> str:
    """Проверяет наличие аппаратного ускорения NVIDIA NVENC."""
    try:
        import subprocess
        res = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True, text=True, errors="replace"
        )
        if "h264_nvenc" in res.stdout:
            return "nvidia"
    except Exception:
        pass
    return "cpu"


def format_seconds(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def main():
    print("=" * 66)
    print("   BATCH UNIQUEIZER X12 — 12 АККАУНТОВ ПО 6 РОЛИКОВ (72 ВИДЕО)")
    print("=" * 66)

    videos = find_videos(INPUT_DIR)
    if not videos:
        print(f"\n[ОШИБКА] В папке input/ нет видеофайлов: {INPUT_DIR}")
        print("Положите исходное видео (например, fhd.mp4) в папку input\\ и запустите снова.")
        sys.exit(1)

    hardware = check_gpu_available()
    total_videos = NUM_ACCOUNTS * VIDEOS_PER_ACCOUNT

    print(f"\n  Найдено исходников в input\\ : {len(videos)}")
    for i, v in enumerate(videos, 1):
        size_mb = os.path.getsize(v) / (1024 * 1024)
        print(f"    {i}. {os.path.basename(v)} ({size_mb:.1f} MB)")

    print(f"\n  Параметры генерации:")
    print(f"    • Аккаунтов         : {NUM_ACCOUNTS} (папки account_01 ... account_{NUM_ACCOUNTS:02d})")
    print(f"    • Роликов на аккаунт: {VIDEOS_PER_ACCOUNT}")
    print(f"    • ВСЕГО файлов      : {total_videos} уникальных роликов")
    print(f"    • Ускорение         : {'NVIDIA GPU (h264_nvenc)' if hardware == 'nvidia' else 'CPU (libx264)'}")
    print(f"    • Формат            : {OUTPUT_FORMAT}")
    print(f"    • Размытый фон      : {'Включен' if BLUR_BACKGROUND else 'Выключен'}")
    print(f"    • Очистка метаданных: {'Включена (-map_metadata -1)' if STRIP_METADATA else 'Выключена'}")
    print(f"    • Диапазон Zoom     : {ZOOM_MIN}% – {ZOOM_MAX}%")
    print(f"    • Диапазон Скорости : {SPEED_MIN}% – {SPEED_MAX}%")
    print(f"    • Выходная папка    : {OUTPUT_DIR}")
    print("-" * 66)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    done = 0
    failed = 0
    start_time = time.time()

    for acc_idx in range(1, NUM_ACCOUNTS + 1):
        acc_folder_name = f"account_{acc_idx:02d}"
        acc_dir = os.path.join(OUTPUT_DIR, acc_folder_name)
        os.makedirs(acc_dir, exist_ok=True)

        print(f"\n>>> Обработка аккаунта [{acc_idx:02d}/{NUM_ACCOUNTS:02d}]: {acc_folder_name}\\")

        for vid_idx in range(1, VIDEOS_PER_ACCOUNT + 1):
            done += 1
            source_video = videos[(vid_idx - 1) % len(videos)]
            source_basename = os.path.splitext(os.path.basename(source_video))[0]

            out_filename = f"{source_basename}_acc{acc_idx:02d}_v{vid_idx:02d}.mp4"
            out_path = os.path.join(acc_dir, out_filename)

            zoom = random.randint(ZOOM_MIN, ZOOM_MAX)
            speed = random.randint(SPEED_MIN, SPEED_MAX)
            filters = list(RANDOM_FILTER_POOL)

            now = time.time()
            elapsed = now - start_time
            avg_per_item = elapsed / max(1, (done - 1)) if done > 1 else 0
            eta_seconds = avg_per_item * (total_videos - (done - 1))
            eta_str = format_seconds(eta_seconds) if done > 1 else "--:--"

            print(f"  [{done:02d}/{total_videos}] {acc_folder_name}\\{out_filename}")
            print(f"       zoom={zoom}% | speed={speed}% | цвет=микро-рандом | ETA: ~{eta_str}")

            try:
                t0 = time.time()
                process_single(
                    in_path=source_video,
                    out_path=out_path,
                    filters=filters,
                    zoom_p=zoom,
                    speed_p=speed,
                    overlay_file=None,
                    overlay_pos="Середина-Центр",
                    output_format=OUTPUT_FORMAT,
                    blur_background=BLUR_BACKGROUND,
                    mute_audio=MUTE_AUDIO,
                    strip_metadata=STRIP_METADATA,
                    hardware=hardware,
                    preset="fast",
                )
                render_sec = time.time() - t0
                out_size_mb = os.path.getsize(out_path) / (1024 * 1024)
                print(f"       [OK] Готово за {render_sec:.1f}с ({out_size_mb:.1f} MB)")
            except Exception as e:
                failed += 1
                print(f"       [ERR] ОШИБКА: {e}")

    total_elapsed = time.time() - start_time
    print("\n" + "=" * 66)
    print("   ИТОГИ ПАКЕТНОЙ ОБРАБОТКИ X12")
    print("=" * 66)
    print(f"  Успешно создано : {done - failed} из {total_videos} роликов")
    if failed > 0:
        print(f"  Ошибок          : {failed}")
    print(f"  Общее время     : {format_seconds(total_elapsed)} ({total_elapsed:.1f} сек)")
    print(f"  Структура папок :")
    for a in range(1, NUM_ACCOUNTS + 1):
        folder = os.path.join(OUTPUT_DIR, f"account_{a:02d}")
        count = len([f for f in os.listdir(folder) if f.endswith('.mp4')]) if os.path.isdir(folder) else 0
        print(f"    • output\\account_{a:02d}\\  -> {count} роликов")
    print("=" * 66)


if __name__ == "__main__":
    main()
