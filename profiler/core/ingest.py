# profiler/core/ingest.py
import os
import hashlib
import json
import subprocess
import tempfile
import cv2
import numpy as np
from typing import Tuple, List, Dict, Any, Optional

class MediaIngest:
    @staticmethod
    def get_file_hash(path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()[:16]

    @staticmethod
    def probe_media(path: str) -> Dict[str, Any]:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_streams", "-show_format",
            "-print_format", "json", path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        data = json.loads(res.stdout)
        
        v_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
        a_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
        
        duration = float(data.get("format", {}).get("duration", 0.0))
        width = int(v_stream.get("width", 0)) if v_stream else 0
        height = int(v_stream.get("height", 0)) if v_stream else 0
        
        # Calculate fps
        fps = 30.0
        if v_stream and "avg_frame_rate" in v_stream:
            try:
                num, den = v_stream["avg_frame_rate"].split("/")
                fps = float(num) / float(den) if float(den) != 0 else 30.0
            except Exception:
                fps = 30.0

        return {
            "duration": duration,
            "width": width,
            "height": height,
            "fps": fps,
            "has_audio": a_stream is not None,
            "size_bytes": int(data.get("format", {}).get("size", 0))
        }

    @staticmethod
    def extract_audio_wav(video_path: str, temp_dir: str) -> Optional[str]:
        wav_path = os.path.join(temp_dir, "audio_16k.wav")
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            wav_path
        ]
        res = subprocess.run(cmd)
        if res.returncode == 0 and os.path.isfile(wav_path):
            return wav_path
        return None

    @staticmethod
    def sample_frames(video_path: str, target_fps: float = 2.0) -> Tuple[List[np.ndarray], List[float]]:
        """
        Samples frames uniformly at target_fps.
        Returns: (frames, timestamps_sec)
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_interval = max(1, int(round(fps / target_fps)))

        frames: List[np.ndarray] = []
        timestamps: List[float] = []

        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % frame_interval == 0:
                t_sec = frame_idx / fps
                frames.append(frame)
                timestamps.append(t_sec)
            frame_idx += 1

        cap.release()
        return frames, timestamps
