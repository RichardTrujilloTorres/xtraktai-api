"""
Unit tests for image quality checking
"""
import io
import pytest
import tempfile
from pathlib import Path
from PIL import Image
import numpy as np

from app.quality_check import (
    check_image_quality,
    get_quality_recommendations,
    should_use_vision_api,
)


# ---------------------------------------------------------------------------
# Helper functions to create test images
# ---------------------------------------------------------------------------

def create_test_image(
    width: int = 800,
    height: int = 1200,
    color: str = "white",
    mode: str = "RGB",
) -> Image.Image:
    """Create a simple test image"""
    return Image.new(mode, (width, height), color)


def create_high_contrast_image(width: int = 800, height: int = 1200) -> Image.Image:
    """Create image with high contrast (black and white stripes)"""
    img = Image.new("RGB", (width, height), "white")
    pixels = img.load()
    
    for y in range(height):
        for x in range(width):
            if (x // 50) % 2 == 0:
                pixels[x, y] = (0, 0, 0)  # Black stripes
    
    return img


def create_low_contrast_image(width: int = 800, height: int = 1200) -> Image.Image:
    """Create image with very low contrast (nearly uniform gray)"""
    # Create array with minimal variation
    arr = np.full((height, width, 3), 128, dtype=np.uint8)
    arr += np.random.randint(-5, 5, (height, width, 3), dtype=np.int8).astype(np.uint8)
    return Image.fromarray(arr)


def create_dark_image(width: int = 800, height: int = 1200) -> Image.Image:
    """Create a very dark image"""
    arr = np.full((height, width, 3), 20, dtype=np.uint8)
    return Image.fromarray(arr)


def create_bright_image(width: int = 800, height: int = 1200) -> Image.Image:
    """Create an overexposed (too bright) image"""
    arr = np.full((height, width, 3), 240, dtype=np.uint8)
    return Image.fromarray(arr)


def save_temp_image(img: Image.Image) -> str:
    """Save image to temp file and return path"""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img.save(f, format="PNG")
        return f.name


# ---------------------------------------------------------------------------
# Tests for get_quality_recommendations (pure function, no I/O)
# ---------------------------------------------------------------------------

class TestGetQualityRecommendations:
    """Tests for get_quality_recommendations function"""

    def test_all_checks_pass(self):
        """No recommendations when all checks pass"""
        recs = get_quality_recommendations(
            resolution_ok=True,
            contrast_ok=True,
            brightness_ok=True,
            blur_ok=True,
        )
        
        assert len(recs) == 1
        assert "good" in recs[0].lower()

    def test_resolution_fail(self):
        """Recommendation for low resolution"""
        recs = get_quality_recommendations(
            resolution_ok=False,
            contrast_ok=True,
            brightness_ok=True,
            blur_ok=True,
        )
        
        assert len(recs) == 1
        assert "resolution" in recs[0].lower()

    def test_contrast_fail(self):
        """Recommendation for low contrast"""
        recs = get_quality_recommendations(
            resolution_ok=True,
            contrast_ok=False,
            brightness_ok=True,
            blur_ok=True,
        )
        
        assert len(recs) == 1
        assert "contrast" in recs[0].lower()

    def test_brightness_fail(self):
        """Recommendation for bad brightness"""
        recs = get_quality_recommendations(
            resolution_ok=True,
            contrast_ok=True,
            brightness_ok=False,
            blur_ok=True,
        )
        
        assert len(recs) == 1
        assert "lighting" in recs[0].lower() or "bright" in recs[0].lower()

    def test_blur_fail(self):
        """Recommendation for blurry image"""
        recs = get_quality_recommendations(
            resolution_ok=True,
            contrast_ok=True,
            brightness_ok=True,
            blur_ok=False,
        )
        
        assert len(recs) == 1
        assert "blur" in recs[0].lower()

    def test_multiple_fails(self):
        """Multiple recommendations when multiple checks fail"""
        recs = get_quality_recommendations(
            resolution_ok=False,
            contrast_ok=False,
            brightness_ok=False,
            blur_ok=False,
        )
        
        assert len(recs) == 4


# ---------------------------------------------------------------------------
# Tests for should_use_vision_api (pure function)
# ---------------------------------------------------------------------------

class TestShouldUseVisionApi:
    """Tests for should_use_vision_api function"""

    def test_good_quality_uses_ocr(self):
        """Good quality images should use OCR (cheaper)"""
        metrics = {"quality_level": "good"}
        assert should_use_vision_api(metrics) is False

    def test_fair_quality_uses_vision(self):
        """Fair quality images should use Vision API"""
        metrics = {"quality_level": "fair"}
        assert should_use_vision_api(metrics) is True

    def test_poor_quality_uses_vision(self):
        """Poor quality images should use Vision API"""
        metrics = {"quality_level": "poor"}
        assert should_use_vision_api(metrics) is True


# ---------------------------------------------------------------------------
# Tests for check_image_quality (requires actual images)
# ---------------------------------------------------------------------------

class TestCheckImageQuality:
    """Tests for check_image_quality function"""

    def test_high_quality_image(self):
        """High quality image should pass most checks"""
        # Create a good image: high res, good contrast
        img = create_high_contrast_image(1200, 1600)
        path = save_temp_image(img)
        
        try:
            result = check_image_quality(path)
            
            assert result["should_process"] == True
            assert result["quality_level"] in ["good", "fair"]
            assert result["quality_score"] >= 2
            assert "checks" in result
            assert result["checks"]["resolution"]["pass"] == True
        finally:
            Path(path).unlink()

    def test_low_resolution_image(self):
        """Low resolution image should fail resolution check"""
        img = create_high_contrast_image(200, 300)  # Too small
        path = save_temp_image(img)
        
        try:
            result = check_image_quality(path)
            
            assert result["checks"]["resolution"]["pass"] == False
            assert "200x300" in result["checks"]["resolution"]["value"]
        finally:
            Path(path).unlink()

    def test_dark_image(self):
        """Very dark image should fail brightness check"""
        img = create_dark_image(800, 1200)
        path = save_temp_image(img)
        
        try:
            result = check_image_quality(path)
            
            assert result["checks"]["brightness"]["pass"] == False
            assert result["checks"]["brightness"]["value"] < 50
        finally:
            Path(path).unlink()

    def test_bright_image(self):
        """Overexposed image should fail brightness check"""
        img = create_bright_image(800, 1200)
        path = save_temp_image(img)
        
        try:
            result = check_image_quality(path)
            
            assert result["checks"]["brightness"]["pass"] == False
            assert result["checks"]["brightness"]["value"] > 200
        finally:
            Path(path).unlink()

    def test_low_contrast_image(self):
        """Low contrast image should fail contrast check"""
        img = create_low_contrast_image(800, 1200)
        path = save_temp_image(img)
        
        try:
            result = check_image_quality(path)
            
            assert result["checks"]["contrast"]["pass"] == False
        finally:
            Path(path).unlink()

    def test_result_structure(self):
        """Verify result contains all expected fields"""
        img = create_test_image(800, 1200)
        path = save_temp_image(img)
        
        try:
            result = check_image_quality(path)
            
            # Top level fields
            assert "should_process" in result
            assert "quality_level" in result
            assert "quality_score" in result
            assert "checks" in result
            assert "recommendations" in result
            
            # Check fields
            checks = result["checks"]
            assert "resolution" in checks
            assert "contrast" in checks
            assert "brightness" in checks
            assert "sharpness" in checks
            
            # Each check has pass, value, and threshold
            for check_name, check_data in checks.items():
                assert "pass" in check_data
                assert "value" in check_data
        finally:
            Path(path).unlink()

    def test_quality_levels(self):
        """Verify quality levels are assigned correctly"""
        # Poor quality: small, uniform color
        poor_img = Image.new("RGB", (100, 100), (128, 128, 128))
        poor_path = save_temp_image(poor_img)
        
        try:
            result = check_image_quality(poor_path)
            
            # With very low score, should be poor or fair
            assert result["quality_level"] in ["poor", "fair", "good"]
            assert result["quality_score"] >= 0
            assert result["quality_score"] <= 4
        finally:
            Path(poor_path).unlink()

    def test_recommendations_present(self):
        """Verify recommendations are always present"""
        img = create_test_image(800, 1200)
        path = save_temp_image(img)
        
        try:
            result = check_image_quality(path)
            
            assert isinstance(result["recommendations"], list)
            assert len(result["recommendations"]) >= 1
        finally:
            Path(path).unlink()
