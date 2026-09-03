# profiler/core/ocr_analyzer.py
import cv2
import numpy as np
from typing import List, Tuple, Dict, Any

class OCRAnalyzer:
    def __init__(self):
        try:
            from rapidocr_onnxruntime import RapidOCR
            self.engine = RapidOCR()
        except Exception as e:
            self.engine = None
            print(f"[WARN] RapidOCR init failed: {e}")

    def analyze(self, frames: List[np.ndarray], max_samples: int = 6) -> Tuple[float, List[str], List[List[float]]]:
        """
        Returns:
            (text_density_pct, detected_tokens, text_box_centroids)
        """
        if not self.engine or not frames:
            return 0.0, [], []

        # Sample up to max_samples evenly
        indices = np.linspace(0, len(frames) - 1, min(len(frames), max_samples), dtype=int)
        
        all_tokens = []
        densities = []
        centroids = []

        keywords = {
            "спред", "детейлинг", "делистинг", "стейкинг", "биржа", "профит", "вывод",
            "связка", "solnexor", "usdt", "binance", "link", "eth", "btc", "курс", "зазор",
            "staking", "delisting", "profit", "spread", "arbitrage"
        }

        for idx in indices:
            frame = frames[idx]
            h, w = frame.shape[:2]
            frame_area = float(h * w)

            try:
                result, _ = self.engine(frame)
            except Exception:
                result = None

            if not result:
                densities.append(0.0)
                continue

            frame_text_area = 0.0
            for item in result:
                dt_boxes, text, score = item
                text_lower = text.lower()
                
                # Check keywords
                for kw in keywords:
                    if kw in text_lower and kw not in all_tokens:
                        all_tokens.append(kw)

                # Compute bounding box area
                pts = np.array(dt_boxes, dtype=np.float32)
                box_w = np.linalg.norm(pts[1] - pts[0])
                box_h = np.linalg.norm(pts[3] - pts[0])
                frame_text_area += (box_w * box_h)

                # Centroid normalized
                cx = float(np.mean(pts[:, 0])) / w
                cy = float(np.mean(pts[:, 1])) / h
                centroids.append([cx, cy])

            density = min(100.0, (frame_text_area / frame_area) * 100.0)
            densities.append(density)

        avg_density = float(np.mean(densities)) if densities else 0.0
        return round(avg_density, 1), all_tokens, centroids
