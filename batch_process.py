# batch_process.py — Быстрая пакетная уникализация под TikTok без GUI
import os
import sys
import random
import time
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.ffmpeg_utils import process_single
from utils.constants import (
    VALID_INPUT_EXTENSIONS, REELS_FORMAT_NAME,
    DEFAULT_OUTPUT_DIR
)

# ─── НАСТРОЙКИ ───────────────────────────────────────────────
COPIES = 6                          # Количество копий каждого ролика
INPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input")
OUTPUT_DIR = DEFAULT_OUTPUT_DIR

ZOOM_MIN = 100                      # Мин. zoom %
ZOOM_MAX = 104                      # Макс. zoom %
SPEED_MIN = 98                      # Мин. скорость %
SPEED_MAX = 102                     # Макс. скорость %

OUTPUT_FORMAT = REELS_FORMAT_NAME   # TikTok/Reels 1080x1920
BLUR_BACKGROUND = True              # Размытый фон для горизонтальных видео
MUTE_AUDIO = False
STRIP_METADATA = True

# Пул фильтров для случайного выбора (каждая копия получит случайный)
RANDOM_FILTER_POOL = [
    "Случ. цвет (яркость/контраст/...)",
]
# ─────────────────────────────────────────────────────────────


def find_videos(directory: str) -> list:
    """Ищет все видеофайлы в указанной папке."""
    videos = []
    for f in os.listdir(directory):
        ext = os.path.splitext(f)[1].lower()
        if ext in VALID_INPUT_EXTENSIONS:
            videos.append(os.path.join(directory, f))
    return sorted(videos)


def main():
    print("=" * 60)
    print("  BATCH UNIQUEIZER — TikTok / Reels")
    print("=" * 60)

    if not os.path.isdir(INPUT_DIR):
        print(f"[ОШИБКА] Папка input не найдена: {INPUT_DIR}")
        sys.exit(1)

    videos = find_videos(INPUT_DIR)
    if not videos:
        print(f"[ОШИБКА] В папке input нет видеофайлов: {INPUT_DIR}")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total = len(videos) * COPIES
    done = 0
    failed = 0
    start_time = time.time()

    print(f"\n  Найдено видео: {len(videos)}")
    print(f"  Копий на видео: {COPIES}")
    print(f"  Всего задач: {total}")
    print(f"  Формат: {OUTPUT_FORMAT}")
    print(f"  Zoom: {ZOOM_MIN}–{ZOOM_MAX}%")
    print(f"  Speed: {SPEED_MIN}–{SPEED_MAX}%")
    print(f"  Размытый фон: {'Да' if BLUR_BACKGROUND else 'Нет'}")
    print(f"  Выход: {OUTPUT_DIR}")
    print("-" * 60)

    for video_path in videos:
        base_name = os.path.basename(video_path)
        name_part, _ = os.path.splitext(base_name)

        for copy_idx in range(1, COPIES + 1):
            done += 1
            zoom = random.randint(ZOOM_MIN, ZOOM_MAX)
            speed = random.randint(SPEED_MIN, SPEED_MAX)
            filters = list(RANDOM_FILTER_POOL)

            out_name = f"{name_part}_tiktok_v{copy_idx}.mp4"
            out_path = os.path.join(OUTPUT_DIR, out_name)

            print(f"\n[{done}/{total}] {base_name} → {out_name}")
            print(f"        zoom={zoom}%  speed={speed}%  filters={filters}")

            try:
                process_single(
                    in_path=video_path,
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
                    preset="fast",
                )
                print(f"        ✓ Готово!")
            except Exception as e:
                failed += 1
                print(f"        ✗ ОШИБКА: {e}")

    elapsed = time.time() - start_time
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    print("\n" + "=" * 60)
    print(f"  ГОТОВО! {done - failed}/{total} успешно, {failed} ошибок")
    print(f"  Время: {mins} мин {secs} сек")
    print(f"  Результат: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
