"""
OpenCV preprocessing for photographed (as opposed to flat-scanned) documents:
grayscale -> denoise -> adaptive threshold -> deskew.

Tesseract's accuracy on a phone photo (skewed, uneven lighting) is materially worse
than on a flat scan; this module exists specifically to close some of that gap.
Call `preprocess(path) -> path_to_cleaned_image` before OCR for camera-captured input.
Flat, already-clean scans/PDFs can skip this and go straight to `ocr.extract_text`.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def _deskew(gray: np.ndarray) -> np.ndarray:
    coords = np.column_stack(np.where(gray < 255))
    if coords.size == 0:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) < 0.5:  # not worth rotating for a near-zero skew
        return gray
    h, w = gray.shape
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(gray, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def preprocess(input_path: str | Path, output_path: str | Path | None = None) -> Path:
    input_path = Path(input_path)
    output_path = Path(output_path) if output_path else input_path.with_name(f"{input_path.stem}_clean.png")

    img = cv2.imread(str(input_path))
    if img is None:
        raise ValueError(f"Could not read image: {input_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11)
    deskewed = _deskew(thresh)

    cv2.imwrite(str(output_path), deskewed)
    return output_path
