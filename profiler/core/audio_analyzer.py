# profiler/core/audio_analyzer.py
import os
import numpy as np
import soundfile as sf
from typing import Tuple, List
from profiler.core.fingerprint import AudioMetrics

class AudioAnalyzer:
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                # Attempt CUDA if possible, test with fallback
                try:
                    m = WhisperModel(self.model_size, device="cuda", compute_type="float16")
                    # Test encode with dummy array to ensure cublas DLLs exist
                    import torch
                    m.model.encode(np.zeros((1, 80, 3000), dtype=np.float32))
                    self._model = m
                except Exception:
                    # Robust fallback to CPU int8 (fast on modern CPUs)
                    self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            except Exception as e:
                print(f"[WARN] Faster-Whisper init failed: {e}")
                self._model = None
        return self._model

    def analyze(self, wav_path: str) -> AudioMetrics:
        if not wav_path or not os.path.isfile(wav_path):
            return AudioMetrics()

        # 1. Spectral Bass / Speech Ratio
        bass_ratio = self._calculate_bass_ratio(wav_path)

        # 2. Faster-Whisper Transcription & Speech Clarity
        model = self._get_model()
        if not model:
            return AudioMetrics(bass_energy_ratio=round(bass_ratio, 1))

        try:
            segments_gen, info = model.transcribe(wav_path, beam_size=2, language=None)
            segments = list(segments_gen)
        except RuntimeError as e:
            # If CUDA runtime failed mid-transcribe (e.g. missing cuBLAS)
            try:
                from faster_whisper import WhisperModel
                self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
                segments_gen, info = self._model.transcribe(wav_path, beam_size=2, language=None)
                segments = list(segments_gen)
            except Exception as ex:
                print(f"[WARN] Whisper fallback failed: {ex}")
                return AudioMetrics(bass_energy_ratio=round(bass_ratio, 1))
        
        full_text_list = []
        logprobs = []
        word_count = 0

        for seg in segments:
            full_text_list.append(seg.text.strip())
            logprobs.append(seg.avg_logprob)
            words = seg.text.strip().split()
            word_count += len(words)

        full_text = " ".join(full_text_list)
        avg_logprob = float(np.mean(logprobs)) if logprobs else -1.0
        clarity = float(np.clip(np.exp(avg_logprob), 0.0, 1.0))

        # Check triggers
        keywords = {
            "спред", "поднял", "заработал", "стейкинг", "биржа", "профит", "вывод",
            "связка", "solnexor", "usdt", "долларов", "баксов", "зазор", "процент",
            "spread", "profit", "arbitrage", "staking"
        }
        text_lower = full_text.lower()
        triggers = [kw for kw in keywords if kw in text_lower]

        return AudioMetrics(
            speech_clarity=round(clarity, 2),
            bass_energy_ratio=round(bass_ratio, 1),
            words_count=word_count,
            trigger_tokens=triggers,
            sample_text=full_text[:180] + ("..." if len(full_text) > 180 else "")
        )

    def _calculate_bass_ratio(self, wav_path: str) -> float:
        try:
            data, sr = sf.read(wav_path)
            if len(data.shape) > 1:
                data = data[:, 0]
            
            n = len(data)
            fft_vals = np.abs(np.fft.rfft(data))
            freqs = np.fft.rfftfreq(n, 1.0 / sr)

            bass_mask = freqs < 150.0
            bass_power = float(np.sum(fft_vals[bass_mask]**2))

            voice_mask = (freqs >= 300.0) & (freqs <= 3400.0)
            voice_power = float(np.sum(fft_vals[voice_mask]**2))

            if voice_power == 0:
                return 0.0

            ratio = (bass_power / voice_power) * 100.0
            return min(100.0, ratio)
        except Exception:
            return 0.0
