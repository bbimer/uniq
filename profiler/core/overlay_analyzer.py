# profiler/core/overlay_analyzer.py
import cv2
import numpy as np
from typing import List, Optional
from profiler.core.fingerprint import OverlayMetrics

class OverlayAnalyzer:
    @staticmethod
    def compare_overlay(base_frames: List[np.ndarray], variant_frames: List[np.ndarray]) -> OverlayMetrics:
        """
        Computes exact empirical overlay metrics by comparing base frames with variant frames.
        """
        n = min(len(base_frames), len(variant_frames))
        if n < 1:
            return OverlayMetrics()

        activities = []
        areas = []
        opacities = []
        motions = []

        target_w, target_h = 360, 640
        prev_diff_gray = None

        for i in range(n):
            b_frame = cv2.resize(base_frames[i], (target_w, target_h))
            v_frame = cv2.resize(variant_frames[i], (target_w, target_h))

            # Absolute difference between base and variant
            diff = cv2.absdiff(v_frame, b_frame)
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

            # Mask of affected pixels (threshold above sensor noise level)
            mask = diff_gray > 8.0
            affected_ratio = float(np.mean(mask)) * 100.0
            areas.append(affected_ratio)

            # Opacity estimate based on mean shift relative to max 255
            if np.any(mask):
                mean_shift = float(np.mean(diff_gray[mask]))
                # Rough alpha estimate: shift / ~128 (assuming average contrast)
                est_alpha = min(1.0, mean_shift / 120.0)
                opacities.append(est_alpha)
            else:
                opacities.append(0.0)

            # Overlay activity (variance across space)
            activities.append(float(np.std(diff_gray)))

            # Overlay motion: difference of differences between frames
            if prev_diff_gray is not None:
                motion_shift = float(np.mean(cv2.absdiff(diff_gray, prev_diff_gray)))
                motions.append(motion_shift)
            prev_diff_gray = diff_gray

        avg_activity = min(100.0, float(np.mean(activities)) * 3.0) if activities else 0.0
        avg_area = float(np.mean(areas)) if areas else 0.0
        avg_opacity = float(np.mean(opacities)) if opacities else 0.0
        avg_motion = min(100.0, float(np.mean(motions)) * 5.0) if motions else 0.0

        return OverlayMetrics(
            overlay_activity=round(avg_activity, 1),
            overlay_area=round(avg_area, 1),
            opacity_estimate=round(avg_opacity, 2),
            overlay_motion=round(avg_motion, 1)
        )
