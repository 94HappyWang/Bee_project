import time
import logging
import cv2
import numpy as np

logger = logging.getLogger("LineCounter")


def segment_intersect(p1, p2, p3, p4):
    """Checks whether line segment (p1-p2) intersects line segment (p3-p4)."""
    def cross_product(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    cp1 = cross_product(p3, p4, p1)
    cp2 = cross_product(p3, p4, p2)
    cp3 = cross_product(p1, p2, p3)
    cp4 = cross_product(p1, p2, p4)

    if ((cp1 > 0 and cp2 < 0) or (cp1 < 0 and cp2 > 0)) and \
       ((cp3 > 0 and cp4 < 0) or (cp3 < 0 and cp4 > 0)):
        return True
    return False


class LineCounter:
    """Dual-Line Sequential State Machine Counter (Line A: Outside, Line B: Hive Entrance).

    Logic:
        - IN  (Enter Hive): Crosses Line A first -> Then crosses Line B within max_time window.
        - OUT (Exit Hive) : Crosses Line B first -> Then crosses Line A within max_time window.
    """

    def __init__(self, line_a=None, line_b=None, max_crossing_time: float = 5.0):
        # Line A: Outdoor end [x1, y1, x2, y2]
        self.line_a = line_a if line_a is not None else [100, 150, 540, 150]
        # Line B: Hive entrance end [x3, y3, x4, y4]
        self.line_b = line_b if line_b is not None else [100, 330, 540, 330]

        self.max_crossing_time = max_crossing_time

        # Counts
        self.in_count = 0
        self.out_count = 0

        # Track State per bee: track_id -> {'first_line': 'A' or 'B', 'timestamp': float}
        self.track_states = {}

        # Last positions of tracks: track_id -> (cx, cy)
        self.prev_positions = {}

        # Visual flash counters for line animation
        self.flash_a = 0
        self.flash_b = 0

    def set_lines(self, line_a, line_b):
        """Updates Line A and Line B coordinates."""
        self.line_a = list(line_a)
        self.line_b = list(line_b)
        logger.info(f"Updated lines: Line A={self.line_a}, Line B={self.line_b}")

    def update(self, tracks: list):
        """Processes active tracks, detects dual-line crossings, and returns new crossing events.

        Args:
            tracks (list): List of active track dicts from BeeTracker.

        Returns:
            list: List of crossing event dicts: [{ 'bee_id': int, 'direction': 'IN'/'OUT', 'duration': float }]
        """
        now = time.time()
        events = []

        # Convert line coordinates to points
        pA1 = (self.line_a[0], self.line_a[1])
        pA2 = (self.line_a[2], self.line_a[3])

        pB1 = (self.line_b[0], self.line_b[1])
        pB2 = (self.line_b[2], self.line_b[3])

        current_ids = set()

        for trk in tracks:
            tid = trk["id"]
            curr_pos = trk["center"]
            current_ids.add(tid)

            if tid in self.prev_positions:
                prev_pos = self.prev_positions[tid]

                # 1. Check intersection with Line A (Outdoor Side)
                crosses_A = segment_intersect(prev_pos, curr_pos, pA1, pA2)

                # 2. Check intersection with Line B (Hive Entrance Side)
                crosses_B = segment_intersect(prev_pos, curr_pos, pB1, pB2)

                if crosses_A:
                    self.flash_a = 10  # trigger visual highlight
                    if tid not in self.track_states:
                        # Started movement from Outside -> Towards Hive
                        self.track_states[tid] = {"first_line": "A", "timestamp": now}
                    elif self.track_states[tid]["first_line"] == "B":
                        # Completed movement: Line B (Hive) -> Line A (Outside) => EXIT!
                        duration = now - self.track_states[tid]["timestamp"]
                        if duration <= self.max_crossing_time:
                            self.out_count += 1
                            events.append({"bee_id": tid, "direction": "OUT", "duration": duration})
                            logger.info(f"🐝 Bee #{tid} EXITED hive (Duration: {duration:.2f}s). Total OUT: {self.out_count}")
                        del self.track_states[tid]

                elif crosses_B:
                    self.flash_b = 10  # trigger visual highlight
                    if tid not in self.track_states:
                        # Started movement from Hive -> Towards Outside
                        self.track_states[tid] = {"first_line": "B", "timestamp": now}
                    elif self.track_states[tid]["first_line"] == "A":
                        # Completed movement: Line A (Outside) -> Line B (Hive) => ENTER!
                        duration = now - self.track_states[tid]["timestamp"]
                        if duration <= self.max_crossing_time:
                            self.in_count += 1
                            events.append({"bee_id": tid, "direction": "IN", "duration": duration})
                            logger.info(f"🐝 Bee #{tid} ENTERED hive (Duration: {duration:.2f}s). Total IN: {self.in_count}")
                        del self.track_states[tid]

            # Update position history
            self.prev_positions[tid] = curr_pos

        # Cleanup lost tracks and expired states
        expired_tids = [tid for tid, st in self.track_states.items() if (now - st["timestamp"]) > self.max_crossing_time]
        for tid in expired_tids:
            del self.track_states[tid]

        lost_tids = set(self.prev_positions.keys()) - current_ids
        for tid in lost_tids:
            del self.prev_positions[tid]

        return events

    def get_counts(self):
        """Returns dict of current counts."""
        return {
            "in_count": self.in_count,
            "out_count": self.out_count,
            "net_count": self.in_count - self.out_count
        }

    def reset_counts(self):
        """Resets counters."""
        self.in_count = 0
        self.out_count = 0
        self.track_states.clear()

    def draw_lines(self, frame: np.ndarray):
        """Draws Line A (Outdoor) and Line B (Hive) with labels on the video frame."""
        # Line A (Outdoor Side - Slate Blue BGR: (255, 134, 58))
        color_a = (255, 134, 58) if self.flash_a <= 0 else (255, 255, 255)
        thickness_a = 2 if self.flash_a <= 0 else 4
        cv2.line(frame, (self.line_a[0], self.line_a[1]), (self.line_a[2], self.line_a[3]), color_a, thickness_a)
        cv2.putText(frame, "Line A (Outdoor)", (self.line_a[0] + 5, self.line_a[1] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_a, 2, cv2.LINE_AA)

        # Line B (Hive Entrance Side - Muted Sage BGR: (143, 157, 42))
        color_b = (143, 157, 42) if self.flash_b <= 0 else (255, 255, 255)
        thickness_b = 2 if self.flash_b <= 0 else 4
        cv2.line(frame, (self.line_b[0], self.line_b[1]), (self.line_b[2], self.line_b[3]), color_b, thickness_b)
        cv2.putText(frame, "Line B (Hive)", (self.line_b[0] + 5, self.line_b[1] + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_b, 2, cv2.LINE_AA)

        if self.flash_a > 0:
            self.flash_a -= 1
        if self.flash_b > 0:
            self.flash_b -= 1

        return frame
