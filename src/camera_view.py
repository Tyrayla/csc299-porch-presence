"""Image-orientation helpers shared by the detector and reference capture."""

import cv2


def rotate_frame(frame, rotation_degrees: int):
    """Rotate a frame clockwise by a supported right-angle increment."""
    rotations = {
        0: None,
        90: cv2.ROTATE_90_CLOCKWISE,
        180: cv2.ROTATE_180,
        270: cv2.ROTATE_90_COUNTERCLOCKWISE,
    }
    if rotation_degrees not in rotations:
        raise ValueError("rotation_degrees must be 0, 90, 180, or 270")
    operation = rotations[rotation_degrees]
    return frame if operation is None else cv2.rotate(frame, operation)
