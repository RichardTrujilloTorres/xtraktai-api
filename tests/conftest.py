"""
Shared pytest fixtures and mock factories for XtraktAI API tests.

All external dependencies (OpenAI, Tesseract) are mocked for:
- Speed: No network calls or OCR processing
- Cost: No OpenAI API charges
- Reliability: Deterministic, no flaky tests
"""

import base64
import io
import json
from datetime import date
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# ---------------------------------------------------------------------------
# Path Constants
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"
IMAGES_DIR = FIXTURES_DIR / "images"
RESPONSES_DIR = FIXTURES_DIR / "responses"


# ---------------------------------------------------------------------------
# FastAPI Test Client
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Create a FastAPI test client."""
    from app.main import app
    
    with TestClient(app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Sample Images
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_image_bytes() -> bytes:
    """Generate a simple test image in memory."""
    img = Image.new("RGB", (800, 1200), color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def sample_image_file(sample_image_bytes) -> io.BytesIO:
    """Return a file-like object for upload testing."""
    return io.BytesIO(sample_image_bytes)


@pytest.fixture
def sample_image_base64(sample_image_bytes) -> str:
    """Return base64 encoded image for Vision API testing."""
    return base64.b64encode(sample_image_bytes).decode("utf-8")


@pytest.fixture
def low_quality_image_bytes() -> bytes:
    """Generate a small, low-quality test image."""
    img = Image.new("RGB", (100, 150), color="gray")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=20)
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Generate minimal PDF bytes for testing."""
    # Minimal valid PDF structure
    pdf_content = b"""%PDF-1.4
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
    return pdf_content


# ---------------------------------------------------------------------------
# Mock Response Factories
# ---------------------------------------------------------------------------

class OpenAIMockFactory:
    """Factory for creating mock OpenAI API responses."""
    
    @staticmethod
    def success_response(
        merchant_name: str = "Test Store",
        total_amount: float = 25.99,
        receipt_date: str = None,
        line_items: list = None,
    ) -> dict[str, Any]:
        """Generate a successful OpenAI parsing response."""
        if receipt_date is None:
            receipt_date = date.today().isoformat()
        
        if line_items is None:
            line_items = [
                {
                    "description": "Test Item 1",
                    "quantity": 1,
                    "unit_price": 10.99,
                    "total_price": 10.99,
                },
                {
                    "description": "Test Item 2",
                    "quantity": 2,
                    "unit_price": 7.50,
                    "total_price": 15.00,
                },
            ]
        
        content = json.dumps({
            "merchant_name": merchant_name,
            "receipt_number": "TEST-123456",
            "receipt_date": receipt_date,
            "receipt_time": "14:30",
            "subtotal": round(total_amount * 0.9, 2),
            "tax_amount": round(total_amount * 0.1, 2),
            "discount_amount": 0.0,
            "total_amount": total_amount,
            "currency": "USD",
            "line_items": line_items,
            "metadata": {
                "store_location": "123 Test Street",
                "payment_method": "Credit Card",
            },
        })
        
        return {
            "id": "chatcmpl-test123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4o-mini",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 150,
                "total_tokens": 250,
            },
        }
    
    @staticmethod
    def partial_response() -> dict[str, Any]:
        """Generate a response with missing optional fields."""
        content = json.dumps({
            "merchant_name": "Unknown Store",
            "total_amount": 19.99,
            "currency": "USD",
        })
        
        return {
            "id": "chatcmpl-test456",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4o-mini",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
        }
    
    @staticmethod
    def error_response(error_message: str = "Rate limit exceeded") -> dict[str, Any]:
        """Generate an error response."""
        return {
            "error": {
                "message": error_message,
                "type": "rate_limit_error",
                "code": "rate_limit_exceeded",
            }
        }


class TesseractMockFactory:
    """Factory for creating mock Tesseract OCR outputs."""
    
    @staticmethod
    def good_quality_text() -> str:
        """Generate clean OCR output from a good quality receipt."""
        return """
WHOLE FOODS MARKET
123 Main Street
San Francisco, CA 94102

Date: 12/05/2024  Time: 14:32

--------------------------------
Organic Bananas      2.5 @ 0.79
                          $1.98
Almond Milk 64oz          $4.99
Sourdough Bread           $5.49
Avocados 3pk              $4.99
--------------------------------

Subtotal                 $17.45
Tax                       $1.49
--------------------------------
TOTAL                    $18.94

VISA ****1234
Auth: 123456

Thank you for shopping!
"""
    
    @staticmethod
    def poor_quality_text() -> str:
        """Generate noisy OCR output from a poor quality receipt."""
        return """
WH0LE F00DS MRKET
l23 Main Str33t
San Franc1sc0, CA 94l02

Dat3: l2/O5/2O24  T1me: l4:32

--------------------------------
0rgan1c 8ananas      2.5 @ O.79
                          $l.98
A1mond M1lk 64oz          $4.99
--------------------------------

T0TAL                    $l8.94
"""
    
    @staticmethod
    def empty_text() -> str:
        """Generate empty OCR output (completely unreadable)."""
        return ""


# ---------------------------------------------------------------------------
# Mock Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def openai_mock_factory() -> OpenAIMockFactory:
    """Provide access to OpenAI mock factory."""
    return OpenAIMockFactory()


@pytest.fixture
def tesseract_mock_factory() -> TesseractMockFactory:
    """Provide access to Tesseract mock factory."""
    return TesseractMockFactory()


@pytest.fixture
def mock_openai_success(openai_mock_factory):
    """Mock OpenAI client to return successful response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "merchant_name": "Test Store",
        "total_amount": 25.99,
        "currency": "USD",
        "receipt_date": date.today().isoformat(),
    })
    
    with patch("openai.OpenAI") as mock_client:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_tesseract(tesseract_mock_factory):
    """Mock Tesseract to return sample OCR text."""
    with patch("pytesseract.image_to_string") as mock_ocr:
        mock_ocr.return_value = tesseract_mock_factory.good_quality_text()
        yield mock_ocr


@pytest.fixture
def mock_pdf_to_image():
    """Mock pdf2image conversion."""
    with patch("pdf2image.convert_from_bytes") as mock_convert:
        # Create a simple test image
        img = Image.new("RGB", (800, 1200), color="white")
        mock_convert.return_value = [img]
        yield mock_convert


# ---------------------------------------------------------------------------
# Environment Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_environment():
    """Ensure test environment variables are set."""
    with patch.dict("os.environ", {
        "OPENAI_API_KEY": "test-api-key-not-real",
        "USE_VISION_API": "false",
    }):
        yield


@pytest.fixture(autouse=True)
def mock_settings():
    """Mock app.config.settings for all tests."""
    mock_config = MagicMock()
    mock_config.OPENAI_API_KEY = "test-api-key-not-real"
    mock_config.MODEL_NAME = "gpt-4o-mini"
    mock_config.USE_VISION_API = False
    mock_config.INCLUDE_RAW_TEXT = True
    mock_config.USE_SMART_ROUTING = False
    
    with patch("app.llm_parser.settings", mock_config), \
         patch("app.vision_parser.settings", mock_config), \
         patch("app.main.settings", mock_config):
        yield mock_config


# ---------------------------------------------------------------------------
# Receipt Data Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_receipt_data() -> dict[str, Any]:
    """Load sample receipt data from fixture file."""
    fixture_path = RESPONSES_DIR / "openai_success.json"
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture
def sample_receipt_data_factory():
    """Factory for generating test receipt data with custom parameters."""
    def _factory(
        merchant_name: str = "Test Store",
        total_amount: float = 25.99,
        num_items: int = 2,
        currency: str = "USD",
    ) -> dict[str, Any]:
        line_items = [
            {
                "description": f"Test Item {i+1}",
                "quantity": 1,
                "unit_price": round(total_amount / num_items, 2),
                "total_price": round(total_amount / num_items, 2),
            }
            for i in range(num_items)
        ]
        
        return {
            "merchant_name": merchant_name,
            "receipt_number": "TEST-123456",
            "receipt_date": date.today().isoformat(),
            "receipt_time": "12:00",
            "subtotal": round(total_amount * 0.9, 2),
            "tax_amount": round(total_amount * 0.1, 2),
            "discount_amount": 0.0,
            "total_amount": total_amount,
            "currency": currency,
            "line_items": line_items,
            "metadata": {
                "store_location": "123 Test St",
                "payment_method": "Credit Card",
            },
        }
    
    return _factory


@pytest.fixture
def mock_openai_success_response(openai_mock_factory) -> dict[str, Any]:
    """Pre-built successful OpenAI response."""
    return openai_mock_factory.success_response()


@pytest.fixture
def mock_ocr_text(tesseract_mock_factory) -> str:
    """Pre-built OCR text output."""
    return tesseract_mock_factory.good_quality_text()


# ---------------------------------------------------------------------------
# Image Quality Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_image_quality_high() -> dict[str, Any]:
    """Mock high quality image assessment."""
    return {
        "resolution_score": 1,
        "contrast_score": 1,
        "brightness_score": 1,
        "sharpness_score": 1,
        "total_score": 4,
        "recommendation": "ocr",
    }


@pytest.fixture
def mock_image_quality_low() -> dict[str, Any]:
    """Mock low quality image assessment."""
    return {
        "resolution_score": 0,
        "contrast_score": 0,
        "brightness_score": 1,
        "sharpness_score": 0,
        "total_score": 1,
        "recommendation": "vision",
    }


# ---------------------------------------------------------------------------
# Validation Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def assert_valid_receipt():
    """Helper to validate receipt data structure."""
    def _validate(receipt: dict[str, Any]) -> None:
        required_fields = ["merchant_name", "total_amount", "currency"]
        
        for field in required_fields:
            assert field in receipt, f"Missing required field: {field}"
        
        assert isinstance(receipt["total_amount"], (int, float)), \
            "total_amount must be a number"
        
        if "line_items" in receipt:
            assert isinstance(receipt["line_items"], list), \
                "line_items must be a list"
    
    return _validate


# ---------------------------------------------------------------------------
# Cleanup Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def cleanup_temp_files(tmp_path):
    """Clean up any temporary files after tests."""
    yield
    # tmp_path is automatically cleaned by pytest
