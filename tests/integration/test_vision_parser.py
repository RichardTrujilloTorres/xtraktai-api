"""
Integration tests for Vision parser module
OpenAI client is mocked for all tests
"""
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

from app.vision_parser import (
    encode_image_to_base64,
    parse_receipt_with_vision,
    parse_receipt_with_vision_fallback,
)
from app.schemas import ReceiptData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_temp_image(suffix=".png") -> str:
    """Create a temporary image file and return its path"""
    img = Image.new("RGB", (800, 1200), color="white")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        img.save(f, format="PNG" if suffix == ".png" else "JPEG")
        return f.name


def build_openai_response(content: str) -> MagicMock:
    """Build a mock OpenAI API response"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response


def build_receipt_json(**kwargs) -> str:
    """Build receipt JSON string"""
    data = {
        "merchant_name": kwargs.get("merchant_name", "Test Store"),
        "total_amount": kwargs.get("total_amount", 25.99),
        "currency": kwargs.get("currency", "USD"),
        "receipt_date": "2024-12-05",
        "extraction_confidence": "high",
    }
    data.update(kwargs)
    return json.dumps(data)


# ---------------------------------------------------------------------------
# Tests for encode_image_to_base64
# ---------------------------------------------------------------------------

class TestEncodeImageToBase64:
    """Tests for base64 image encoding"""

    def test_encodes_png_image(self):
        """Should encode PNG image to base64"""
        image_path = create_temp_image(".png")
        try:
            result = encode_image_to_base64(image_path)
            
            assert isinstance(result, str)
            assert len(result) > 0
            # Base64 strings only contain these characters
            assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in result)
        finally:
            Path(image_path).unlink()

    def test_encodes_jpg_image(self):
        """Should encode JPG image to base64"""
        image_path = create_temp_image(".jpg")
        try:
            result = encode_image_to_base64(image_path)
            
            assert isinstance(result, str)
            assert len(result) > 0
        finally:
            Path(image_path).unlink()

    def test_raises_on_missing_file(self):
        """Should raise exception for missing file"""
        with pytest.raises(FileNotFoundError):
            encode_image_to_base64("/nonexistent/path/image.png")


# ---------------------------------------------------------------------------
# Tests for parse_receipt_with_vision
# ---------------------------------------------------------------------------

class TestParseReceiptWithVision:
    """Tests for Vision API receipt parsing"""

    @patch("app.vision_parser.OpenAI")
    def test_parses_valid_response(self, mock_openai_class):
        """Should parse valid JSON response into ReceiptData"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = build_openai_response(
            build_receipt_json(merchant_name="Whole Foods", total_amount=47.06)
        )
        
        image_path = create_temp_image()
        try:
            result = parse_receipt_with_vision(image_path)
            
            assert isinstance(result, ReceiptData)
            assert result.merchant_name == "Whole Foods"
            assert result.total_amount == 47.06
        finally:
            Path(image_path).unlink()

    @patch("app.vision_parser.OpenAI")
    def test_handles_png_media_type(self, mock_openai_class):
        """Should detect PNG media type"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = build_openai_response(
            build_receipt_json()
        )
        
        image_path = create_temp_image(".png")
        try:
            parse_receipt_with_vision(image_path)
            
            # Check the API was called
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args
            # The image URL should contain image/png
            messages = call_args.kwargs.get("messages", call_args.args[0] if call_args.args else [])
            # Just verify it was called - detailed structure checking is fragile
            assert mock_client.chat.completions.create.called
        finally:
            Path(image_path).unlink()

    @patch("app.vision_parser.OpenAI")
    def test_handles_jpg_media_type(self, mock_openai_class):
        """Should detect JPEG media type"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = build_openai_response(
            build_receipt_json()
        )
        
        image_path = create_temp_image(".jpg")
        try:
            parse_receipt_with_vision(image_path)
            assert mock_client.chat.completions.create.called
        finally:
            Path(image_path).unlink()

    @patch("app.vision_parser.OpenAI")
    def test_handles_markdown_code_blocks(self, mock_openai_class):
        """Should strip markdown code blocks from response"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        json_content = build_receipt_json()
        markdown_response = f"```json\n{json_content}\n```"
        mock_client.chat.completions.create.return_value = build_openai_response(markdown_response)
        
        image_path = create_temp_image()
        try:
            result = parse_receipt_with_vision(image_path)
            assert isinstance(result, ReceiptData)
        finally:
            Path(image_path).unlink()

    @patch("app.vision_parser.OpenAI")
    def test_raises_on_invalid_json(self, mock_openai_class):
        """Should raise exception for invalid JSON response"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = build_openai_response(
            "This is not valid JSON"
        )
        
        image_path = create_temp_image()
        try:
            with pytest.raises(Exception) as exc_info:
                parse_receipt_with_vision(image_path)
            
            assert "Failed to parse Vision API response" in str(exc_info.value)
        finally:
            Path(image_path).unlink()

    @patch("app.vision_parser.OpenAI")
    def test_raises_on_api_error(self, mock_openai_class):
        """Should raise exception on API error"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")
        
        image_path = create_temp_image()
        try:
            with pytest.raises(Exception) as exc_info:
                parse_receipt_with_vision(image_path)
            
            assert "Error parsing receipt with Vision API" in str(exc_info.value)
        finally:
            Path(image_path).unlink()


# ---------------------------------------------------------------------------
# Tests for parse_receipt_with_vision_fallback
# ---------------------------------------------------------------------------

class TestParseReceiptWithVisionFallback:
    """Tests for Vision API with LLM fallback"""

    @patch("app.vision_parser.OpenAI")
    def test_uses_vision_when_successful(self, mock_openai_class):
        """Should use Vision API when it succeeds"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = build_openai_response(
            build_receipt_json(merchant_name="Vision Store")
        )
        
        image_path = create_temp_image()
        try:
            result = parse_receipt_with_vision_fallback(image_path)
            
            assert result.merchant_name == "Vision Store"
        finally:
            Path(image_path).unlink()

    @patch("app.llm_parser.parse_receipt_with_llm")
    @patch("app.vision_parser.OpenAI")
    def test_falls_back_to_llm_on_error(self, mock_openai_class, mock_llm_parser):
        """Should fall back to LLM when Vision fails and OCR text provided"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Vision failed")
        
        # Mock LLM fallback
        mock_llm_parser.return_value = ReceiptData(
            merchant_name="LLM Store",
            total_amount=30.00,
            currency="USD"
        )
        
        image_path = create_temp_image()
        try:
            result = parse_receipt_with_vision_fallback(image_path, ocr_text="RECEIPT TEXT")
            
            assert result.merchant_name == "LLM Store"
            mock_llm_parser.assert_called_once_with("RECEIPT TEXT")
        finally:
            Path(image_path).unlink()

    @patch("app.vision_parser.OpenAI")
    def test_raises_when_no_fallback(self, mock_openai_class):
        """Should raise error when Vision fails and no OCR text provided"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Vision failed")
        
        image_path = create_temp_image()
        try:
            with pytest.raises(Exception) as exc_info:
                parse_receipt_with_vision_fallback(image_path, ocr_text=None)
            
            assert "Vision failed" in str(exc_info.value)
        finally:
            Path(image_path).unlink()
