"""
Lightweight face tracking based on bounding-box IoU.

This is intentionally simpler than full SORT: no Kalman filter and no scipy
dependency. It gives stable short-lived track IDs for webcam attendance frames.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np


@dataclass
class Track:
    id: int
    bbox: List[int]
    age: int = 0
    hits: int = 1
    missed: int = 0

    def predict(self) -> List[int]:
        self.age += 1
        self.missed += 1
        return self.bbox

    def update(self, bbox: List[int]) -> None:
        self.bbox = bbox
        self.hits += 1
        self.missed = 0


class FaceTracker:
    """Assign stable temporary IDs to face detections across frames."""

    def __init__(self, max_age: int = 10, min_hits: int = 1, iou_threshold: float = 0.3):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.tracks: List[Track] = []
        self.next_id = 1
        self.frame_count = 0

    def update(self, detections: List[Dict]) -> List[Dict]:
        self.frame_count += 1

        for track in self.tracks:
            track.predict()

        detection_boxes = [self._normalize_bbox(det["bbox"]) for det in detections]
        matches, unmatched_detections = self._match(detection_boxes)

        detection_to_track: Dict[int, Track] = {}
        for track_index, detection_index in matches:
            track = self.tracks[track_index]
            track.update(detection_boxes[detection_index])
            detection_to_track[detection_index] = track

        for detection_index in unmatched_detections:
            track = Track(self.next_id, detection_boxes[detection_index])
            self.next_id += 1
            self.tracks.append(track)
            detection_to_track[detection_index] = track

        self.tracks = [track for track in self.tracks if track.missed <= self.max_age]

        tracked = []
        for detection_index, detection in enumerate(detections):
            result = detection.copy()
            track = detection_to_track.get(detection_index)
            if track and track.hits >= self.min_hits:
                result["track_id"] = track.id
                result["track_age"] = track.age
                result["track_hits"] = track.hits
            tracked.append(result)

        return tracked

    def reset(self) -> None:
        self.tracks = []
        self.next_id = 1
        self.frame_count = 0

    def active_count(self) -> int:
        return len(self.tracks)

    def active_track_ids(self) -> List[int]:
        return [track.id for track in self.tracks]

    def _match(self, detection_boxes: List[List[int]]) -> Tuple[List[Tuple[int, int]], List[int]]:
        if not self.tracks:
            return [], list(range(len(detection_boxes)))

        if not detection_boxes:
            return [], []

        iou_matrix = np.zeros((len(self.tracks), len(detection_boxes)), dtype=np.float32)
        for track_index, track in enumerate(self.tracks):
            for detection_index, bbox in enumerate(detection_boxes):
                iou_matrix[track_index, detection_index] = self.iou(track.bbox, bbox)

        matches: List[Tuple[int, int]] = []
        unmatched_tracks = set(range(len(self.tracks)))
        unmatched_detections = set(range(len(detection_boxes)))

        while unmatched_tracks and unmatched_detections:
            best_track: Optional[int] = None
            best_detection: Optional[int] = None
            best_iou = self.iou_threshold

            for track_index in unmatched_tracks:
                for detection_index in unmatched_detections:
                    value = float(iou_matrix[track_index, detection_index])
                    if value >= best_iou:
                        best_iou = value
                        best_track = track_index
                        best_detection = detection_index

            if best_track is None or best_detection is None:
                break

            matches.append((best_track, best_detection))
            unmatched_tracks.remove(best_track)
            unmatched_detections.remove(best_detection)

        return matches, sorted(unmatched_detections)

    @staticmethod
    def iou(bbox_a: List[int], bbox_b: List[int]) -> float:
        ax, ay, aw, ah = bbox_a
        bx, by, bw, bh = bbox_b

        ax2 = ax + aw
        ay2 = ay + ah
        bx2 = bx + bw
        by2 = by + bh

        ix1 = max(ax, bx)
        iy1 = max(ay, by)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)

        intersection = max(0, ix2 - ix1) * max(0, iy2 - iy1)
        union = (aw * ah) + (bw * bh) - intersection
        if union <= 0:
            return 0.0
        return intersection / union

    @staticmethod
    def _normalize_bbox(bbox: List[int]) -> List[int]:
        x, y, w, h = bbox
        return [int(x), int(y), int(w), int(h)]
