"""
Face crop utilities used before live inference.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image


@dataclass
class FaceCropResult:
    image: Image.Image
    applied: bool
    box: Optional[Tuple[int, int, int, int]]
    original_size: Tuple[int, int]
    cropped_size: Tuple[int, int]
    detected_count: int = 0
    rejected_count: int = 0
    reason: str = "face_crop_disabled"


_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
_EYE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_eye.xml"
)


def _expand_box(x: int, y: int, w: int, h: int, width: int, height: int, margin: float):
    pad_x = int(w * margin)
    pad_y = int(h * margin)
    left = max(0, x - pad_x)
    top = max(0, y - pad_y)
    right = min(width, x + w + pad_x)
    bottom = min(height, y + h + pad_y)
    return left, top, right, bottom


def _has_eye_evidence(gray: np.ndarray, face: Tuple[int, int, int, int]) -> bool:
    x, y, w, h = (int(value) for value in face)
    aspect_ratio = w / h if h else 0
    if aspect_ratio < 0.72 or aspect_ratio > 1.35:
        return False

    upper_face = gray[y:y + int(h * 0.68), x:x + w]
    if upper_face.size == 0:
        return False

    min_eye = max(8, int(min(w, h) * 0.12))
    eyes = _EYE_CASCADE.detectMultiScale(
        upper_face,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(min_eye, min_eye),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    return len(eyes) > 0


# SUNUM-ANAHTAR: face crop - internet gorsellerinde once yuz bolgesini bulup modele oyle veriyoruz.
def crop_largest_face(image: Image.Image, margin: float = 0.35) -> FaceCropResult:
    rgb_image = image.convert("RGB")
    width, height = rgb_image.size

    np_image = np.array(rgb_image)
    gray = cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)
    gray = cv2.equalizeHist(gray)

    faces = _CASCADE.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=6,
        minSize=(40, 40),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )

    detected_count = int(len(faces))
    accepted_faces = [face for face in faces if _has_eye_evidence(gray, face)]

    if len(accepted_faces) == 0:
        return FaceCropResult(
            image=rgb_image,
            applied=False,
            box=None,
            original_size=(width, height),
            cropped_size=(width, height),
            detected_count=detected_count,
            rejected_count=detected_count,
            reason="no_face_detected" if detected_count == 0 else "face_candidates_rejected",
        )

    x, y, w, h = (int(value) for value in max(accepted_faces, key=lambda face: face[2] * face[3]))
    box = _expand_box(x, y, w, h, width, height, margin)
    cropped = rgb_image.crop(box)

    return FaceCropResult(
        image=cropped,
        applied=True,
        box=box,
        original_size=(width, height),
        cropped_size=cropped.size,
        detected_count=detected_count,
        rejected_count=detected_count - len(accepted_faces),
        reason="face_detected",
    )
