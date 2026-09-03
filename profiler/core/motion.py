# profiler/core/motion.py
import cv2
import numpy as np
from typing import List, Tuple
from profiler.core.fingerprint import MotionComponents

class MotionAnalyzer:
    @staticmethod
    def analyze(frames: List[np.ndarray], timestamps: List[float]) -> MotionComponents:
        if len(frames) < 2:
            return MotionComponents()

        camera_motions: List[float] = []
        content_motions: List[float] = []
        visual_variances: List[float] = []
        is_static_flags: List[bool] = []
        hook_motions: List[float] = []
        scene_cuts: int = 0

        # Downsample resolution for optical flow computation speed
        target_w, target_h = 360, 640
        prev_gray = cv2.cvtColor(cv2.resize(frames[0], (target_w, target_h)), cv2.COLOR_BGR2GRAY)

        for i in range(1, len(frames)):
            curr_raw = frames[i]
            t_sec = timestamps[i]
            curr_gray = cv2.cvtColor(cv2.resize(curr_raw, (target_w, target_h)), cv2.COLOR_BGR2GRAY)

            # Scene change detection based on histogram correlation
            hist_prev = cv2.calcHist([prev_gray], [0], None, [32], [0, 256])
            hist_curr = cv2.calcHist([curr_gray], [0], None, [32], [0, 256])
            hist_corr = cv2.compareHist(hist_prev, hist_curr, cv2.HISTCMP_CORREL)

            if hist_corr < 0.45:
                scene_cuts += 1

            # Dense Optical Flow (Farneback)
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, curr_gray, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )

            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])

            # Global camera motion: approximate with median displacement
            med_u = float(np.median(flow[..., 0]))
            med_v = float(np.median(flow[..., 1]))
            cam_mag = float(np.sqrt(med_u**2 + med_v**2))
            camera_motions.append(cam_mag)

            # Content motion: deviation from global camera motion
            residual_mag = np.abs(mag - cam_mag)
            content_mag = float(np.mean(residual_mag))
            content_motions.append(content_mag)

            # Visual variance: standard deviation of frame pixel differences
            frame_diff = cv2.absdiff(curr_gray, prev_gray)
            v_var = float(np.std(frame_diff))
            visual_variances.append(v_var)

            # Staticity: threshold below which frame is considered essentially static
            total_motion = float(np.mean(mag))
            is_static = total_motion < 0.8
            is_static_flags.append(is_static)

            # Hook dynamism: motion in the first 3 seconds
            if t_sec <= 3.0:
                hook_motions.append(total_motion)

            prev_gray = curr_gray

        duration = timestamps[-1] if timestamps else 1.0
        cuts_per_min = (scene_cuts / max(1.0, duration)) * 60.0

        # Normalization to 0-100 scale
        avg_cam = min(100.0, float(np.mean(camera_motions)) * 12.0) if camera_motions else 0.0
        avg_content = min(100.0, float(np.mean(content_motions)) * 15.0) if content_motions else 0.0
        avg_variance = min(100.0, float(np.mean(visual_variances)) * 2.5) if visual_variances else 0.0
        static_pct = (sum(is_static_flags) / max(1, len(is_static_flags))) * 100.0
        hook_dyn = min(100.0, float(np.mean(hook_motions)) * 15.0) if hook_motions else avg_cam

        return MotionComponents(
            camera_motion=round(avg_cam, 1),
            content_motion=round(avg_content, 1),
            scene_change_rate=round(cuts_per_min, 1),
            visual_variance=round(avg_variance, 1),
            staticity_pct=round(static_pct, 1),
            hook_dynamism_0_3s=round(hook_dyn, 1)
        )
