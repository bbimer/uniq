# profiler/core/fingerprint.py
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any

@dataclass
class ScreenDominanceComponents:
    edge_density: float = 0.0           # 0-100: density of sharp UI edges (Canny)
    rectangular_structure: float = 0.0  # 0-100: presence of geometric box structures (Hough lines / contours)
    screen_texture: float = 0.0         # 0-100: LCD/monitor surface uniformity & contrast
    temporal_stability: float = 0.0     # 0-100: persistence of fixed UI frame elements
    ocr_concentration: float = 0.0      # 0-100: clustering of text in UI layout blocks
    composite: float = 0.0              # 0-100: weighted composite score

@dataclass
class MotionComponents:
    camera_motion: float = 0.0          # 0-100: global camera / handheld shift
    content_motion: float = 0.0         # 0-100: local motion inside active regions
    scene_change_rate: float = 0.0      # cuts / transitions per minute
    visual_variance: float = 0.0        # 0-100: pixel-level standard deviation & temporal flux
    staticity_pct: float = 0.0          # 0-100: percentage of frames with near-zero motion
    hook_dynamism_0_3s: float = 0.0     # 0-100: motion intensity in the first 3 seconds

@dataclass
class AudioMetrics:
    speech_clarity: float = 0.0         # 0.0 - 1.0: average confidence / logprob of Whisper transcription
    bass_energy_ratio: float = 0.0      # 0-100: ratio of sub-bass (<150Hz) power to voice band (300-3400Hz)
    words_count: int = 0
    trigger_tokens: List[str] = field(default_factory=list)
    sample_text: str = ""

@dataclass
class OverlayMetrics:
    overlay_activity: float = 0.0       # 0-100: temporal delta introduced by overlay
    overlay_area: float = 0.0           # 0-100: estimated percentage of frame affected by overlay
    opacity_estimate: float = 0.0       # 0.0 - 1.0: estimated alpha level
    overlay_motion: float = 0.0         # 0-100: motion dynamics attributable to overlay layer

@dataclass
class FingerprintVector:
    video_id: str
    file_path: str
    file_hash: str
    duration_sec: float
    width: int
    height: int
    fps: float
    screen_dominance: ScreenDominanceComponents
    motion: MotionComponents
    audio: AudioMetrics
    overlay: Optional[OverlayMetrics] = None
    archetype: str = "Unknown"

    def determine_archetype(self) -> str:
        sd = self.screen_dominance.composite
        st = self.motion.staticity_pct
        vv = self.motion.visual_variance
        cm = self.motion.camera_motion

        if self.overlay and self.overlay.overlay_activity > 20:
            return "Mixed Dynamic Media (Overlay Layered)"
        elif sd > 65.0 and st > 50.0:
            return "Static Screencast (Monitor Focus)"
        elif sd > 50.0 and vv > 35.0:
            return "Dynamic Screencast (Active UI / Motion)"
        elif cm > 35.0:
            return "Handheld Live Action"
        elif vv > 45.0:
            return "Mixed Dynamic Media"
        else:
            return "Standard UGC Screencast"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
