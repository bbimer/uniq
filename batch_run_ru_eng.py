# batch_run_ru_eng.py — 6 RU + 12 ENG Unique Videos
import os
import sys
import time
import random
import subprocess

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

INPUT_DIR = r"C:\Users\root\Desktop\uniq\input"
OUTPUT_DIR = r"C:\Users\root\Desktop\uniq\output"

TASKS = [
    {"source": "RU.mp4", "folder": "RU", "prefix": "RU_v", "count": 6},
    {"source": "ENG.mp4", "folder": "ENG", "prefix": "ENG_v", "count": 12},
]

# Настройки качества под ~26-28 МБ при 1080x1920 60fps
BITRATE = "7000k"
MAXRATE = "8200k"
BUFSIZE = "14000k"
AUDIO_BITRATE = "192k"

def format_sec(s):
    m = int(s // 60)
    sec = int(s % 60)
    return f"{m:02d}:{sec:02d}"

def main():
    print("=" * 66)
    print("   GENERATING: 6 RU + 12 ENG UNIQUE VIDEOS (18 TOTAL)")
    print("=" * 66)

    total_tasks = sum(t["count"] for t in TASKS)
    done = 0
    failed = 0
    start_time = time.time()

    for task in TASKS:
        src_path = os.path.join(INPUT_DIR, task["source"])
        if not os.path.isfile(src_path):
            print(f"[ERROR] Source file not found: {src_path}")
            continue

        target_dir = os.path.join(OUTPUT_DIR, task["folder"])
        os.makedirs(target_dir, exist_ok=True)

        print(f"\n>>> Target folder: output\\{task['folder']}\\ ({task['count']} videos)")

        for idx in range(1, task["count"] + 1):
            done += 1
            out_filename = f"{task['prefix']}{idx:02d}.mp4"
            out_path = os.path.join(target_dir, out_filename)

            br = f"{random.uniform(-0.015, 0.015):.4f}"
            ct = f"{random.uniform(0.98, 1.02):.4f}"
            sat = f"{random.uniform(0.98, 1.02):.4f}"
            hue = f"{random.uniform(-0.5, 0.5):.2f}"
            zoom = f"{random.uniform(1.01, 1.03):.4f}"
            speed = f"{random.uniform(0.99, 1.01):.4f}"

            vf = f"eq=brightness={br}:contrast={ct}:saturation={sat},hue=h={hue},scale=iw*{zoom}:ih*{zoom}:flags=bicubic,crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,format=yuv420p"
            af = f"atempo={speed}"

            cmd = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
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
