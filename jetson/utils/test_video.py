import os
import cv2
import numpy as np


def create_sample_bee_corridor_video(output_path="data/sample_corridor.mp4", num_frames=300):
    """Creates a synthetic video simulating bees moving through a corridor across Line A and Line B."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if os.path.exists(output_path):
        return output_path

    w, h = 640, 480
    fps = 30
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    # Bee positions (entering and exiting)
    bees = [
        {"start_y": 50, "speed_y": 3, "x": 200, "dir": 1},   # Bee 1 entering (top to bottom)
        {"start_y": 420, "speed_y": -4, "x": 400, "dir": -1}, # Bee 2 exiting (bottom to top)
        {"start_y": 80, "speed_y": 2, "x": 320, "dir": 1}    # Bee 3 entering
    ]

    for f in range(num_frames):
        # Create background corridor
        frame = np.ones((h, w, 3), dtype=np.uint8) * 40
        # Draw wooden corridor texture
        cv2.rectangle(frame, (80, 0), (560, h), (70, 60, 50), -1)
        cv2.line(frame, (80, 0), (80, h), (120, 100, 80), 4)
        cv2.line(frame, (560, 0), (560, h), (120, 100, 80), 4)

        # Draw moving bees (yellow ovals)
        for b in bees:
            cy = (b["start_y"] + f * b["speed_y"] * b["dir"]) % h
            cx = b["x"] + int(np.sin(f * 0.1) * 15)

            # Draw bee body
            cv2.ellipse(frame, (cx, cy), (12, 8), 0, 0, 360, (0, 215, 255), -1)
            # Stripes
            cv2.line(frame, (cx - 4, cy - 6), (cx - 4, cy + 6), (0, 0, 0), 2)
            cv2.line(frame, (cx + 4, cy - 6), (cx + 4, cy + 6), (0, 0, 0), 2)
            # Wings
            cv2.ellipse(frame, (cx - 8, cy - 8), (8, 4), 30, 0, 360, (230, 230, 230), -1)
            cv2.ellipse(frame, (cx + 8, cy - 8), (8, 4), -30, 0, 360, (230, 230, 230), -1)

        out.write(frame)

    out.release()
    print(f"Sample test video created at: {output_path}")
    return output_path
