"""
API tests for FastAPI endpoints
All external dependencies are mocked
"""
import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.schemas import ReceiptData


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Create FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def sample_image_bytes():
    """Generate a simple test image"""
    img = Image.new("RGB", (800, 1200), color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def sample_pdf_bytes():
    """Generate minimal PDF bytes"""
    return b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >> endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer << /Size 4 /Root 1 0 R >>
startxref
196
%%EOF"""


# ---------------------------------------------------------------------------
# Tests for GET /
# ---------------------------------------------------------------------------

class TestRootEndpoint:
    """Tests for root health check endpoint"""

    def test_returns_healthy_status(self, client):
        """Should return healthy status"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Receipt Processing API"
        assert data["version"] == "1.0.0"


# ---------------------------------------------------------------------------
# Tests for GET /health
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    """Tests for detailed health check endpoint"""

    @patch("app.main.settings")
    def test_returns_health_details_configured(self, mock_settings, client):
        """Should return health details when configured"""
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.USE_VISION_API = True
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "ocr" in data
        assert "llm" in data
        assert "vision_api" in data

    @patch("app.main.settings")
    def test_shows_not_configured_when_no_key(self, mock_settings, client):
        """Should show not configured when no API key"""
        mock_settings.OPENAI_API_KEY = None
        mock_settings.USE_VISION_API = False
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "not configured" in data["llm"]


# ---------------------------------------------------------------------------
# Tests for POST /check-quality
# ---------------------------------------------------------------------------

class TestCheckQualityEndpoint:
    """Tests for quality check endpoint"""

    @patch("app.main.should_use_vision_api")
    @patch("app.main.check_image_quality")
    def test_checks_image_quality(self, mock_quality, mock_should_vision, client, sample_image_bytes):
        """Should return quality metrics for images"""
        mock_quality.return_value = {
            "quality_level": "good",
            "quality_score": 4,
            "should_process": True,
            "checks": {},
            "recommendations": ["Image quality is good!"]
        }
        mock_should_vision.return_value = False
        
        response = client.post(
            "/check-quality",
            files={"file": ("receipt.png", sample_image_bytes, "image/png")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "quality" in data
        assert data["recommended_method"] == "ocr"

    @patch("app.main.should_use_vision_api")
    @patch("app.main.check_image_quality")
    def test_recommends_vision_for_poor_quality(self, mock_quality, mock_should_vision, client, sample_image_bytes):
        """Should recommend vision API for poor quality"""
        mock_quality.return_value = {
            "quality_level": "poor",
            "quality_score": 1,
            "should_process": False,
            "checks": {},
            "recommendations": ["Image is blurry"]
        }
        mock_should_vision.return_value = True
        
        response = client.post(
            "/check-quality",
            files={"file": ("receipt.png", sample_image_bytes, "image/png")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["recommended_method"] == "vision_api"

    def test_pdf_quality_check_not_available(self, client, sample_pdf_bytes):
        """Should return message for PDF files"""
        response = client.post(
            "/check-quality",
            files={"file": ("receipt.pdf", sample_pdf_bytes, "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "not available for PDFs" in data["message"]
        assert data["recommended_method"] == "ocr"

    def test_rejects_unsupported_file_type(self, client):
        """Should reject unsupported file types"""
        response = client.post(
            "/check-quality",
            files={"file": ("receipt.txt", b"text content", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    @patch("app.main.check_image_quality")
    def test_handles_quality_check_error(self, mock_quality, client, sample_image_bytes):
        """Should return 500 on quality check error"""
        mock_quality.side_effect = Exception("Quality check failed")
        
        response = client.post(
            "/check-quality",
            files={"file": ("receipt.png", sample_image_bytes, "image/png")}
        )
        
        assert response.status_code == 500
        assert "Error checking quality" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Tests for POST /process-receipt
# ---------------------------------------------------------------------------

class TestProcessReceiptEndpoint:
    """Tests for main receipt processing endpoint"""

    @patch("app.main.settings")
    @patch("app.main.parse_receipt_with_vision")
    @patch("app.main.check_image_quality")
    def test_processes_image_with_vision_api(
        self, mock_quality, mock_vision, mock_settings, client, sample_image_bytes
    ):
        """Should process image with Vision API"""
        mock_settings.USE_VISION_API = True
        mock_settings.USE_SMART_ROUTING = False
        mock_settings.INCLUDE_RAW_TEXT = False
        
        mock_quality.return_value = {
            "quality_level": "good",
            "quality_score": 4,
        }
        mock_vision.return_value = ReceiptData(
            merchant_name="Test Store",
            total_amount=25.99,
            currency="USD"
        )
        
        response = client.post(
            "/process-receipt",
            files={"file": ("receipt.png", sample_image_bytes, "image/png")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["merchant_name"] == "Test Store"

    @patch("app.main.settings")
    @patch("app.main.parse_receipt_with_llm")
    @patch("app.main.extract_text_from_file")
    @patch("app.main.check_image_quality")
    def test_falls_back_to_ocr_when_vision_fails(
        self, mock_quality, mock_ocr, mock_llm, mock_settings, client, sample_image_bytes
    ):
        """Should fall back to OCR when Vision API fails"""
        mock_settings.USE_VISION_API = True
        mock_settings.USE_SMART_ROUTING = False
        mock_settings.INCLUDE_RAW_TEXT = True
        
        mock_quality.return_value = {"quality_level": "good", "quality_score": 4}
        
        # Make Vision fail
        with patch("app.main.parse_receipt_with_vision", side_effect=Exception("Vision failed")):
            mock_ocr.return_value = "STORE NAME\nTOTAL $25.99"
            mock_llm.return_value = ReceiptData(
                merchant_name="OCR Store",
                total_amount=25.99,
                currency="USD"
            )
            
            response = client.post(
                "/process-receipt",
                files={"file": ("receipt.png", sample_image_bytes, "image/png")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["merchant_name"] == "OCR Store"

    @patch("app.main.settings")
    @patch("app.main.parse_receipt_with_llm")
    @patch("app.main.extract_text_from_file")
    def test_processes_with_ocr_when_vision_disabled(
        self, mock_ocr, mock_llm, mock_settings, client, sample_image_bytes
    ):
        """Should use OCR when Vision API is disabled"""
        mock_settings.USE_VISION_API = False
        mock_settings.USE_SMART_ROUTING = False
        mock_settings.INCLUDE_RAW_TEXT = False
        
        mock_ocr.return_value = "STORE NAME\nTOTAL $30.00"
        mock_llm.return_value = ReceiptData(
            merchant_name="OCR Only Store",
            total_amount=30.00,
            currency="USD"
        )
        
        response = client.post(
            "/process-receipt",
            files={"file": ("receipt.png", sample_image_bytes, "image/png")},
            params={"skip_quality_check": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["merchant_name"] == "OCR Only Store"

    @patch("app.main.settings")
    @patch("app.main.check_image_quality")
    def test_rejects_low_quality_image(self, mock_quality, mock_settings, client, sample_image_bytes):
        """Should reject images with quality score < 2"""
        mock_settings.USE_VISION_API = True
        
        mock_quality.return_value = {
            "quality_level": "poor",
            "quality_score": 1,
            "recommendations": ["Image is too blurry"]
        }
        
        response = client.post(
            "/process-receipt",
            files={"file": ("receipt.png", sample_image_bytes, "image/png")}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "quality_too_low"

    @patch("app.main.settings")
    @patch("app.main.parse_receipt_with_vision")
    def test_skips_quality_check_when_requested(
        self, mock_vision, mock_settings, client, sample_image_bytes
    ):
        """Should skip quality check when skip_quality_check=True"""
        mock_settings.USE_VISION_API = True
        mock_settings.USE_SMART_ROUTING = False
        mock_settings.INCLUDE_RAW_TEXT = False
        
        mock_vision.return_value = ReceiptData(
            merchant_name="Skip Quality Store",
            total_amount=50.00,
            currency="USD"
        )
        
        response = client.post(
            "/process-receipt",
            files={"file": ("receipt.png", sample_image_bytes, "image/png")},
            params={"skip_quality_check": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["merchant_name"] == "Skip Quality Store"

    def test_rejects_unsupported_file_type(self, client):
        """Should reject unsupported file types"""
        response = client.post(
            "/process-receipt",
            files={"file": ("receipt.txt", b"text content", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    @patch("app.main.settings")
    @patch("app.main.extract_text_from_file")
    def test_returns_error_for_empty_ocr(self, mock_ocr, mock_settings, client, sample_image_bytes):
        """Should return error when OCR extracts no text"""
        mock_settings.USE_VISION_API = False
        mock_settings.USE_SMART_ROUTING = False
        
        mock_ocr.return_value = ""  # Empty OCR result
        
        response = client.post(
            "/process-receipt",
            files={"file": ("receipt.png", sample_image_bytes, "image/png")},
            params={"skip_quality_check": True}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Could not extract" in data["message"]

    @patch("app.main.settings")
    @patch("app.main.parse_receipt_with_llm")
    @patch("app.main.extract_text_from_file")
    def test_returns_partial_failure_for_empty_merchant(
        self, mock_ocr, mock_llm, mock_settings, client, sample_image_bytes
    ):
        """Should return partial failure when merchant name is empty"""
        mock_settings.USE_VISION_API = False
        mock_settings.USE_SMART_ROUTING = False
        mock_settings.INCLUDE_RAW_TEXT = True
        
        mock_ocr.return_value = "SOME TEXT HERE"
        mock_llm.return_value = ReceiptData(
            merchant_name="",  # Empty merchant
            total_amount=25.00,
            currency="USD"
        )
        
        response = client.post(
            "/process-receipt",
            files={"file": ("receipt.png", sample_image_bytes, "image/png")},
            params={"skip_quality_check": True}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "partial_failure"

    @patch("app.main.settings")
    @patch("app.main.parse_receipt_with_llm")
    @patch("app.main.extract_text_from_file")
    def test_returns_partial_failure_on_llm_error(
        self, mock_ocr, mock_llm, mock_settings, client, sample_image_bytes
    ):
        """Should return partial failure when LLM parsing fails"""
        mock_settings.USE_VISION_API = False
        mock_settings.USE_SMART_ROUTING = False
        mock_settings.INCLUDE_RAW_TEXT = True
        
        mock_ocr.return_value = "RECEIPT TEXT"
        mock_llm.side_effect = Exception("LLM parsing failed")
        
        response = client.post(
            "/process-receipt",
            files={"file": ("receipt.png", sample_image_bytes, "image/png")},
            params={"skip_quality_check": True}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "partial_failure"
        assert "parsing failed" in data["message"]

    @patch("app.main.settings")
    @patch("app.main.parse_receipt_with_llm")
    @patch("app.main.extract_text_from_file")
    def test_processes_pdf_file(
        self, mock_ocr, mock_llm, mock_settings, client, sample_pdf_bytes
    ):
        """Should process PDF files"""
        mock_settings.USE_VISION_API = False
        mock_settings.USE_SMART_ROUTING = False
        mock_settings.INCLUDE_RAW_TEXT = False
        
        mock_ocr.return_value = "PDF RECEIPT\nTOTAL $100.00"
        mock_llm.return_value = ReceiptData(
            merchant_name="PDF Store",
            total_amount=100.00,
            currency="USD"
        )
        
        response = client.post(
            "/process-receipt",
            files={"file": ("receipt.pdf", sample_pdf_bytes, "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["merchant_name"] == "PDF Store"

    @patch("app.main.settings")
    @patch("app.main.should_use_vision_api")
    @patch("app.main.parse_receipt_with_vision")
    @patch("app.main.check_image_quality")
    def test_smart_routing_uses_vision_for_poor_quality(
        self, mock_quality, mock_vision, mock_should_vision, mock_settings, client, sample_image_bytes
    ):
        """Should use Vision API for poor quality when smart routing enabled"""
        mock_settings.USE_VISION_API = True
        mock_settings.USE_SMART_ROUTING = True
        mock_settings.INCLUDE_RAW_TEXT = False
        
        mock_quality.return_value = {"quality_level": "fair", "quality_score": 2}
        mock_should_vision.return_value = True
        mock_vision.return_value = ReceiptData(
            merchant_name="Smart Route Store",
            total_amount=75.00,
            currency="USD"
        )
        
        response = client.post(
            "/process-receipt",
            files={"file": ("receipt.png", sample_image_bytes, "image/png")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["merchant_name"] == "Smart Route Store"


# ---------------------------------------------------------------------------
# Tests for error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Tests for global error handling"""

    def test_handles_missing_file(self, client):
        """Should return 422 when no file provided"""
        response = client.post("/process-receipt")
        
        # FastAPI returns 422 for validation errors
        assert response.status_code == 422
