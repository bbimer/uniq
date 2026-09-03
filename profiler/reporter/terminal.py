# profiler/reporter/terminal.py
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from profiler.core.fingerprint import FingerprintVector, OverlayMetrics

console = Console()

class TerminalReporter:
    @staticmethod
    def render_single(fp: FingerprintVector, exp_id: str = ""):
        console.print()
        
        # Header Panel
        title_text = Text(f"FORMAT FINGERPRINT: {fp.archetype.upper()}", style="bold white on blue")
        header = f"[bold cyan]File:[/bold cyan] {fp.file_path}\n" \
                 f"[bold cyan]Resolution:[/bold cyan] {fp.width}x{fp.height} @ {fp.fps:.1f}fps  |  " \
                 f"[bold cyan]Duration:[/bold cyan] {fp.duration_sec:.1f}s  |  " \
                 f"[bold cyan]Hash:[/bold cyan] {fp.file_hash}\n" \
                 f"[bold cyan]Experiment ID:[/bold cyan] [green]{exp_id}[/green]"
        console.print(Panel(header, title=title_text, box=box.ROUNDED, expand=False))

        # Metrics Table
        table = Table(box=box.SIMPLE_HEAVY, title="[bold]Observed Physical Signals[/bold]")
        table.add_column("Category", style="bold yellow", width=24)
        table.add_column("Metric", style="white", width=26)
        table.add_column("Observed Value", style="bold green", width=18)
        table.add_column("Interpretation / Note", style="dim white")

        # Screen Dominance
        sd = fp.screen_dominance
        table.add_row("SCREEN DOMINANCE", "Composite Score", f"{sd.composite:.1f}%", "Overall software UI/display footprint")
        table.add_row("", "├─ Edge Density", f"{sd.edge_density:.1f}%", "Sharp UI borders (Canny/Sobel)")
        table.add_row("", "├─ Rect Structure", f"{sd.rectangular_structure:.1f}%", "Geometric horizontal/vertical lines")
        table.add_row("", "├─ Screen Texture", f"{sd.screen_texture:.1f}%", "Uniform panels & LCD contrast")
        table.add_row("", "├─ Temporal Stability", f"{sd.temporal_stability:.1f}%", "Stationary UI headers/elements")
        table.add_row("", "└─ OCR Concentration", f"{sd.ocr_concentration:.1f}%", "Text clustering into tabular blocks")

        # Motion & Dynamics
        m = fp.motion
        table.add_section()
        table.add_row("MOTION DYNAMICS", "Staticity (No Motion)", f"{m.staticity_pct:.1f}%", "Share of duration with near-zero motion")
        table.add_row("", "Camera Motion (Global)", f"{m.camera_motion:.1f}", "Handheld / tripod global drift")
        table.add_row("", "Content Motion (Local)", f"{m.content_motion:.1f}", "Active elements inside windows")
        table.add_row("", "Visual Variance", f"{m.visual_variance:.1f}", "Pixel standard deviation flux")
        table.add_row("", "Hook Dynamism (0-3s)", f"{m.hook_dynamism_0_3s:.1f}", "Initial movement velocity")
        table.add_row("", "Scene Cut Rate", f"{m.scene_change_rate:.1f} / min", "Hard scene switches")

        # Audio
        a = fp.audio
        table.add_section()
        table.add_row("AUDIO SIGNALS", "Speech Clarity", f"{a.speech_clarity * 100:.1f}%", "ASR model transcription confidence")
        table.add_row("", "Sub-Bass Energy (<150Hz)", f"{a.bass_energy_ratio:.1f}%", "Ratio of sub-bass to speech power")
        table.add_row("", "Words Spoken", str(a.words_count), "Total transcript word count")
        
        triggers_str = ", ".join(a.trigger_tokens) if a.trigger_tokens else "None detected"
        table.add_row("", "Financial Stop-words", triggers_str, "Terms flagged by ASR")

        console.print(table)
        console.print(f"[dim]Sample Transcript:[/dim] \"{a.sample_text}\"")
        console.print()

    @staticmethod
    def render_comparison(base: FingerprintVector, var: FingerprintVector, overlay: OverlayMetrics):
        console.print()
        title_text = Text("A/B FORMAT FINGERPRINT BENCHMARK", style="bold black on yellow")
        
        table = Table(box=box.ROUNDED, title=title_text)
        table.add_column("METRIC", style="bold white", width=28)
        table.add_column("BASE (Original)", justify="right", style="cyan", width=18)
        table.add_column("VARIANT (New)", justify="right", style="magenta", width=18)
        table.add_column("Δ (DELTA)", justify="right", width=16)

        def delta_row(label: str, v1: float, v2: float, is_pct: bool = True, invert_color: bool = False):
            d = v2 - v1
            pct_s = "%" if is_pct else ""
            
            # Color logic: positive change
            if d > 0:
                col = "red" if invert_color else "green"
                d_str = f"[{col}]+{d:.1f}{pct_s}[/{col}]"
            elif d < 0:
                col = "green" if invert_color else "red"
                d_str = f"[{col}]{d:.1f}{pct_s}[/{col}]"
            else:
                d_str = f"[dim]0.0{pct_s}[/dim]"

            table.add_row(label, f"{v1:.1f}{pct_s}", f"{v2:.1f}{pct_s}", d_str)

        # Screen Dominance
        delta_row("SCREEN DOMINANCE", base.screen_dominance.composite, var.screen_dominance.composite, is_pct=True, invert_color=True)
        delta_row("  ├─ Edge Density", base.screen_dominance.edge_density, var.screen_dominance.edge_density, is_pct=True, invert_color=True)
        delta_row("  ├─ Rect Structure", base.screen_dominance.rectangular_structure, var.screen_dominance.rectangular_structure, is_pct=True, invert_color=True)
        delta_row("  └─ Temporal Stability", base.screen_dominance.temporal_stability, var.screen_dominance.temporal_stability, is_pct=True, invert_color=True)
        
        # Motion
        table.add_section()
        delta_row("STATICITY (Near-zero)", base.motion.staticity_pct, var.motion.staticity_pct, is_pct=True, invert_color=True)
        delta_row("VISUAL VARIANCE", base.motion.visual_variance, var.motion.visual_variance, is_pct=False, invert_color=False)
        delta_row("CAMERA MOTION", base.motion.camera_motion, var.motion.camera_motion, is_pct=False, invert_color=False)
        delta_row("CONTENT MOTION", base.motion.content_motion, var.motion.content_motion, is_pct=False, invert_color=False)
        delta_row("HOOK DYNAMISM (0-3s)", base.motion.hook_dynamism_0_3s, var.motion.hook_dynamism_0_3s, is_pct=False, invert_color=False)

        # Audio
        table.add_section()
        delta_row("SPEECH CLARITY", base.audio.speech_clarity * 100, var.audio.speech_clarity * 100, is_pct=True, invert_color=True)
        delta_row("SUB-BASS RATIO", base.audio.bass_energy_ratio, var.audio.bass_energy_ratio, is_pct=True, invert_color=False)

        # Overlay Layer specifically
        table.add_section()
        table.add_row("[bold yellow]OVERLAY LAYER IMPACT[/bold yellow]", "", "", "")
        table.add_row("  ├─ Overlay Activity", "-", f"{overlay.overlay_activity:.1f}", "[yellow]Added motion[/yellow]")
        table.add_row("  ├─ Overlay Area Coverage", "-", f"{overlay.overlay_area:.1f}%", "[yellow]Pixel footprint[/yellow]")
        table.add_row("  ├─ Opacity Estimate", "-", f"{overlay.opacity_estimate:.2f} alpha", "[yellow]Blending density[/yellow]")
        table.add_row("  └─ Overlay Motion Factor", "-", f"{overlay.overlay_motion:.1f}", "[yellow]Internal flux[/yellow]")

        console.print(table)

        # Archetype comparison
        arch_panel = f"[bold cyan]{base.archetype}[/bold cyan]  [bold yellow]──►[/bold yellow]  [bold magenta]{var.archetype}[/bold magenta]"
        console.print(Panel(arch_panel, title="[bold]FORMAT ARCHETYPE TRANSITION[/bold]", box=box.ROUNDED, expand=False))
        console.print()
