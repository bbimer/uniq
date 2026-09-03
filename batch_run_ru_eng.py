import os
import time
import random
import subprocess

INPUT_DIR = "input"
OUTPUT_DIR = "output"

TASKS = [
    {"source": "RU.mp4", "folder": "RU", "prefix": "RU_v", "count": 6},
    {"source": "ENG.mp4", "folder": "ENG", "prefix": "ENG_v", "count": 12},
]

BITRATE = "7000k"
MAXRATE = "8500k"
BUFSIZE = "14000k"
AUDIO_BITRATE = "192k"

def format_sec(sec: float) -> str:
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m:02d}:{s:02d}"

def main():
    print("=" * 66)
    print("   NVIDIA NVENC BATCH UNIQUEIZATION (RU: 6, ENG: 12) + PITCH & AUDIO SHIFT")
    print("=" * 66)

    total_tasks = sum(t["count"] for t in TASKS)
    done = 0
    failed = 0
    start_time = time.time()

    for task in TASKS:
        src_path = os.path.join(INPUT_DIR, task["source"])
        if not os.path.isfile(src_path):
            print(f"[!] Source missing: {src_path}")
            continue

        target_dir = os.path.join(OUTPUT_DIR, task["folder"])
        os.makedirs(target_dir, exist_ok=True)

        print(f"\n>>> Target folder: output\\{task['folder']}\\ ({task['count']} videos)")

        for idx in range(1, task["count"] + 1):
            done += 1
            out_filename = f"{task['prefix']}{idx:02d}.mp4"
            out_path = os.path.join(target_dir, out_filename)

            # 1. Сдвиг старта (рандомный срез 0.12..0.35 сек) — ломает Frame 0 / Hook
            start_offset = round(random.uniform(0.12, 0.35), 3)

            # 2. Пространственный сдвиг кадра (зум + асимметричный кроп)
            zoom = round(random.uniform(1.025, 1.045), 4)
            shift_x = random.randint(-10, 10)
            shift_y = random.randint(-15, 15)

            # 3. Цветовой спектр и гамма
            br = f"{random.uniform(-0.015, 0.015):.4f}"
            ct = f"{random.uniform(0.98, 1.02):.4f}"
            sat = f"{random.uniform(0.98, 1.02):.4f}"
            gamma = f"{random.uniform(0.97, 1.03):.4f}"
            hue = f"{random.uniform(-0.6, 0.6):.2f}"

            # 4. Аудио-хэш: темп + сдвиг тона голоса (pitch) + эквалайзер спектра
            pitch = f"{random.uniform(0.982, 1.018):.4f}"
            speed = f"{random.uniform(0.985, 1.015):.4f}"
            bass_g = f"{random.uniform(-1.5, 1.5):.2f}"
            treble_g = f"{random.uniform(-1.5, 1.5):.2f}"

            # Фильтр видео: eq + hue + micro-grain noise + scale + asymmetric crop
            vf = (
                f"eq=brightness={br}:contrast={ct}:saturation={sat}:gamma={gamma},"
                f"hue=h={hue},"
                f"noise=c0s=2:c0f=u:allf=t,"
                f"scale=iw*{zoom}:ih*{zoom}:flags=bicubic,"
                f"crop=1080:1920:(in_w-1080)/2+{shift_x}:(in_h-1920)/2+{shift_y},"
                f"format=yuv420p"
            )

            # Фильтр аудио: rubberband pitch shift + EQ + micro-tempo
            af = f"rubberband=pitch={pitch},bass=g={bass_g}:f=150,treble=g={treble_g}:f=3000,atempo={speed}"

            cmd = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
                "-ss", str(start_offset),
                "-i", src_path,
                "-vf", vf,
                "-af", af,
                "-c:v", "h264_nvenc", "-preset", "p4",
                "-b:v", BITRATE, "-maxrate", MAXRATE, "-bufsize", BUFSIZE,
                "-c:a", "aac", "-b:a", AUDIO_BITRATE,
                "-map_metadata", "-1", "-map_chapters", "-1",
                "-movflags", "+faststart",
                out_path
            ]

            now = time.time()
            elapsed = now - start_time
            avg_per_item = elapsed / max(1, (done - 1)) if done > 1 else 0
            eta_seconds = avg_per_item * (total_tasks - (done - 1))
            eta_str = format_sec(eta_seconds) if done > 1 else "--:--"

            print(f"  [{done:02d}/{total_tasks:02d}] output\\{task['folder']}\\{out_filename} (ETA: {eta_str})...", end="", flush=True)

            try:
                t0 = time.time()
                subprocess.run(cmd, check=True)
                t_render = time.time() - t0
                sz_mb = os.path.getsize(out_path) / (1024 * 1024)
                print(f" [OK] {t_render:.1f}s ({sz_mb:.1f} MB)")
            except Exception as e:
                failed += 1
                print(f" [ERR]: {e}")

    total_time = time.time() - start_time
    print("\n" + "=" * 66)
    print("   COMPLETE! SUCCESSFULLY GENERATED:")
    print("=" * 66)
    for task in TASKS:
        folder = os.path.join(OUTPUT_DIR, task["folder"])
        cnt = len([f for f in os.listdir(folder) if f.endswith('.mp4')]) if os.path.isdir(folder) else 0
        print(f"   • output\\{task['folder']}\\  -> {cnt} videos")
    print(f"   Total time: {format_sec(total_time)} ({total_time:.1f} s)")
    print("=" * 66)

if __name__ == "__main__":
    main()
