"""
Image quality validation for receipt processing
Checks if image meets minimum quality standards
"""
from PIL import Image
import numpy as np


def check_image_quality(image_path: str) -> dict:
    """
    Validate image quality before processing

    Args:
        image_path: Path to image file

    Returns:
        Dict with quality metrics and pass/fail status
    """
    img = Image.open(image_path)

    # Convert to numpy array for analysis
    img_array = np.array(img.convert('L'))  # Grayscale

    # Check 1: Resolution
    width, height = img.size
    min_dimension = min(width, height)
    max_dimension = max(width, height)

    resolution_ok = min_dimension >= 600  # At least 600px on shortest side

    # Check 2: Contrast (standard deviation of pixel values)
    contrast = np.std(img_array)
    contrast_ok = contrast >= 30  # Minimum contrast threshold

    # Check 3: Brightness (mean pixel value)
    brightness = np.mean(img_array)
    brightness_ok = 50 <= brightness <= 200  # Not too dark or too bright

    # Check 4: Blur detection (Laplacian variance)
    from PIL import ImageFilter
    img_filtered = img.filter(ImageFilter.FIND_EDGES)
    edges = np.array(img_filtered)
    blur_score = np.var(edges)
    blur_ok = blur_score >= 100  # Higher = sharper

    # Overall quality assessment
    quality_score = sum([resolution_ok, contrast_ok, brightness_ok, blur_ok])

    if quality_score >= 3:
        quality_level = "good"
        should_process = True
    elif quality_score == 2:
        quality_level = "fair"
        should_process = True  # But warn user
    else:
        quality_level = "poor"
        should_process = False  # Reject

    return {
        "should_process": should_process,
        "quality_level": quality_level,
        "quality_score": quality_score,
        "checks": {
            "resolution": {
                "pass": resolution_ok,
                "value": f"{width}x{height}",
                "min_required": "600px min dimension"
            },
            "contrast": {
                "pass": contrast_ok,
                "value": round(contrast, 2),
                "min_required": 30
            },
            "brightness": {
                "pass": brightness_ok,
                "value": round(brightness, 2),
                "range_required": "50-200"
            },
            "sharpness": {
                "pass": blur_ok,
                "value": round(blur_score, 2),
                "min_required": 100
            }
        },
        "recommendations": get_quality_recommendations(
            resolution_ok, contrast_ok, brightness_ok, blur_ok
        )
    }


def get_quality_recommendations(resolution_ok, contrast_ok, brightness_ok, blur_ok):
    """Generate helpful recommendations based on failed checks"""
    recommendations = []

    if not resolution_ok:
        recommendations.append("📸 Image resolution too low - use a better camera or get closer")

    if not contrast_ok:
        recommendations.append("☀️ Low contrast - ensure good lighting, avoid shadows")

    if not brightness_ok:
        recommendations.append("💡 Adjust lighting - image is too dark or too bright")

    if not blur_ok:
        recommendations.append("🎯 Image is blurry - hold camera steady and ensure focus")

    if not recommendations:
        recommendations.append("✅ Image quality is good!")

    return recommendations


def should_use_vision_api(quality_metrics: dict) -> bool:
    """
    Decide whether to use Vision API based on quality

    Vision API is more expensive but better for poor quality.
    Use it when image quality is fair or poor.

    Args:
        quality_metrics: Output from check_image_quality

    Returns:
        True if should use Vision API, False for OCR
    """
    quality_level = quality_metrics["quality_level"]

    # Use Vision API for fair/poor quality
    # Use OCR for good quality (cheaper)
    return quality_level in ["fair", "poor"]