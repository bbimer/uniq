# run_profile.py — Media Profiler & Format Fingerprint Engine
import os
import sys
import argparse
import tempfile
import time

# Ensure UTF-8 output on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from profiler.core.ingest import MediaIngest
from profiler.core.motion import MotionAnalyzer
from profiler.core.screen_detector import ScreenDetector
from profiler.core.ocr_analyzer import OCRAnalyzer
from profiler.core.audio_analyzer import AudioAnalyzer
from profiler.core.overlay_analyzer import OverlayAnalyzer
from profiler.core.fingerprint import FingerprintVector
from profiler.reporter.terminal import TerminalReporter, console
from profiler.storage.experiment_store import ExperimentStore

def profile_single_video(video_path: str, ocr_engine: OCRAnalyzer, audio_engine: AudioAnalyzer) -> FingerprintVector:
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    with console.status(f"[bold cyan]Ingesting & sampling frames:[/bold cyan] {os.path.basename(video_path)}..."):
        probe = MediaIngest.probe_media(video_path)
        file_hash = MediaIngest.get_file_hash(video_path)
        frames, timestamps = MediaIngest.sample_frames(video_path, target_fps=2.0)

    with console.status("[bold cyan]Analyzing motion dynamics (Optical Flow)..."):
        motion_comps = MotionAnalyzer.analyze(frames, timestamps)

    with console.status("[bold cyan]Running OCR & layout text scanner..."):
        text_density, ocr_tokens, ocr_boxes = ocr_engine.analyze(frames)

    with console.status("[bold cyan]Computing screen & UI dominance..."):
        screen_comps = ScreenDetector.analyze(frames, ocr_boxes)

    # Audio extraction & analysis
    with tempfile.TemporaryDirectory() as temp_dir:
        wav_path = MediaIngest.extract_audio_wav(video_path, temp_dir)
        with console.status("[bold cyan]Running Whisper ASR & spectral bass analysis..."):
            audio_comps = audio_engine.analyze(wav_path) if wav_path else audio_engine.analyze("")

    # Merge OCR tokens into trigger tokens if any
    for t in ocr_tokens:
        if t not in audio_comps.trigger_tokens:
            audio_comps.trigger_tokens.append(f"ocr:{t}")

    fp = FingerprintVector(
        video_id=os.path.basename(video_path),
        file_path=os.path.abspath(video_path),
        file_hash=file_hash,
        duration_sec=probe["duration"],
        width=probe["width"],
        height=probe["height"],
        fps=probe["fps"],
        screen_dominance=screen_comps,
        motion=motion_comps,
        audio=audio_comps
    )
    fp.archetype = fp.determine_archetype()
    return fp

def main():
    parser = argparse.ArgumentParser(description="Media Profiler & Format Fingerprint Engine")
    parser.add_argument("video", nargs="?", help="Path to video file to profile")
    parser.add_argument("--compare", nargs=2, metavar=("BASE", "VARIANT"), help="A/B Benchmark comparison between two videos")
    parser.add_argument("--list", action="store_true", help="List recorded experiments")
    parser.add_argument("--update", metavar="EXP_ID", help="Update outcomes for an experiment ID")
    parser.add_argument("--views-1h", type=int, help="Views after 1 hour")
    parser.add_argument("--views-24h", type=int, help="Views after 24 hours")
    parser.add_argument("--watch-time", type=float, help="Average watch time in seconds")
    parser.add_argument("--completion-rate", type=float, help="Completion rate percentage (0-100)")
    parser.add_argument("--shares", type=int, help="Number of shares")
    parser.add_argument("--saves", type=int, help="Number of saves")
    parser.add_argument("--reach", type=int, help="Recommendation reach")

    args = parser.parse_args()
    store = ExperimentStore()

    # Outcome update mode
    if args.update:
        outcomes = {
            "views_1h": args.views_1h,
            "views_24h": args.views_24h,
            "avg_watch_time": args.watch_time,
            "completion_rate": args.completion_rate,
            "shares": args.shares,
            "saves": args.saves,
            "recommendation_reach": args.reach
        }
        success = store.update_outcomes(args.update, outcomes)
        if success:
            console.print(f"[bold green]Updated outcomes for experiment:[/bold green] {args.update}")
        else:
            console.print(f"[bold red]Experiment ID not found:[/bold red] {args.update}")
        return

    # List experiments mode
    if args.list:
        records = store.list_experiments()
        console.print(f"\n[bold]Logged Experiments ({len(records)} total):[/bold]")
        for r in records[-10:]:
            exp_id = r["experiment_id"]
            fn = r["file_name"]
            arch = r["fingerprint"]["archetype"]
            out = r["outcomes"]
            v24 = out.get("views_24h") or "--"
            console.print(f" • [cyan]{exp_id}[/cyan] | {fn} | [yellow]{arch}[/yellow] | Views 24h: [green]{v24}[/green]")
        console.print()
        return

    # Initialize shared AI analyzers
    ocr_engine = OCRAnalyzer()
    audio_engine = AudioAnalyzer(model_size="base")

    # A/B Comparison Mode
    if args.compare:
        base_path, var_path = args.compare
        console.print(f"\n[bold yellow]PROFILING A/B BENCHMARK:[/bold yellow] {os.path.basename(base_path)} vs {os.path.basename(var_path)}")

        fp_base = profile_single_video(base_path, ocr_engine, audio_engine)
        fp_var = profile_single_video(var_path, ocr_engine, audio_engine)

        # Overlay analysis
        with console.status("[bold cyan]Comparing overlay layers between base and variant..."):
            frames_base, _ = MediaIngest.sample_frames(base_path, target_fps=2.0)
            frames_var, _ = MediaIngest.sample_frames(var_path, target_fps=2.0)
            overlay_metrics = OverlayAnalyzer.compare_overlay(frames_base, frames_var)
            fp_var.overlay = overlay_metrics
            fp_var.archetype = fp_var.determine_archetype()

        # Log both experiments
        exp_id_base = store.log_fingerprint(fp_base)
        exp_id_var = store.log_fingerprint(fp_var, variant_of=fp_base.file_hash)

        # Render Rich A/B Table
        TerminalReporter.render_comparison(fp_base, fp_var, overlay_metrics)
        console.print(f"[dim]Base Exp ID: {exp_id_base}  |  Variant Exp ID: {exp_id_var}[/dim]\n")
        return

    # Single Video Profile Mode
    if args.video:
        fp = profile_single_video(args.video, ocr_engine, audio_engine)
        exp_id = store.log_fingerprint(fp)
        TerminalReporter.render_single(fp, exp_id=exp_id)
        return

    parser.print_help()

if __name__ == "__main__":
    main()
