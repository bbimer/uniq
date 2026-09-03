# profiler/core/screen_detector.py
import cv2
import numpy as np
from typing import List
from profiler.core.fingerprint import ScreenDominanceComponents

class ScreenDetector:
    @staticmethod
    def analyze(frames: List[np.ndarray], ocr_boxes: List[List[float]] = None) -> ScreenDominanceComponents:
        if not frames:
            return ScreenDominanceComponents()

        edge_densities = []
        rect_structures = []
        texture_scores = []
        
        target_w, target_h = 360, 640
        grays = [cv2.cvtColor(cv2.resize(f, (target_w, target_h)), cv2.COLOR_BGR2GRAY) for f in frames]

        for gray in grays:
            # 1. Edge density (Horizontal & Vertical UI borders)
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            edge_mag = np.sqrt(sobelx**2 + sobely**2)
            edge_dens = float(np.mean(edge_mag > 40.0)) * 100.0
            edge_densities.append(edge_dens)

            # 2. Rectangular structure (Hough Lines & Contours)
            canny = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(canny, 1, np.pi / 180, threshold=80, minLineLength=50, maxLineGap=10)
            hv_lines = 0
            if lines is not None:
                for line in lines:
                    coords = line.flatten()
                    if len(coords) >= 4:
                        x1, y1, x2, y2 = coords[:4]
                        dx = abs(x2 - x1)
                        dy = abs(y2 - y1)
                        if dx > dy * 4 or dy > dx * 4:
                            hv_lines += 1
            rect_score = min(100.0, hv_lines * 2.5)
            rect_structures.append(rect_score)

            # 3. Screen texture: high contrast step-edges & flat panels typical of software UI
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            lap_var = float(np.var(laplacian))
            flat_regions = float(np.mean(np.abs(laplacian) < 5.0)) * 100.0
            tex_score = min(100.0, flat_regions * 0.9 + (lap_var / 100.0) * 0.3)
            texture_scores.append(tex_score)

        # 4. Temporal stability of pixels (UI headers/footers staying identical across time)
        stack = np.array(grays)  # (N, H, W)
        pixel_temporal_std = np.std(stack, axis=0)  # (H, W)
        static_pixel_ratio = float(np.mean(pixel_temporal_std < 8.0)) * 100.0

        # 5. OCR concentration (spatial clustering of text into columns/tables)
        ocr_conc = 50.0
        if ocr_boxes and len(ocr_boxes) > 0:
            xs = [b[0] for b in ocr_boxes]
            if len(xs) > 3:
                x_std = float(np.std(xs))
                ocr_conc = max(10.0, min(100.0, 100.0 - (x_std * 50.0)))

        avg_edge = min(100.0, float(np.mean(edge_densities)) * 4.0)
        avg_rect = min(100.0, float(np.mean(rect_structures)))
        avg_tex = min(100.0, float(np.mean(texture_scores)))
        temp_stab = min(100.0, static_pixel_ratio)

        # Composite score
        composite = (
            0.25 * avg_edge +
            0.25 * avg_rect +
            0.20 * avg_tex +
            0.20 * temp_stab +
            0.10 * ocr_conc
        )

        return ScreenDominanceComponents(
            edge_density=round(avg_edge, 1),
            rectangular_structure=round(avg_rect, 1),
            screen_texture=round(avg_tex, 1),
            temporal_stability=round(temp_stab, 1),
            ocr_concentration=round(ocr_conc, 1),
            composite=round(composite, 1)
        )
