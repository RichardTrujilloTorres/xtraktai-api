"""
Smoke tests to verify the test infrastructure is working correctly.

Run with: pytest tests/test_smoke.py -v
"""

import pytest


class TestInfrastructure:
    """Verify test fixtures and infrastructure work correctly."""

    def test_sample_receipt_data_fixture(self, sample_receipt_data):
        """Verify sample_receipt_data fixture loads correctly."""
        assert sample_receipt_data["merchant_name"] == "Whole Foods Market"
        assert sample_receipt_data["total_amount"] == 47.06
        assert len(sample_receipt_data["line_items"]) == 2

    def test_sample_receipt_factory(self, sample_receipt_data_factory):
        """Verify receipt factory generates valid data."""
        receipt = sample_receipt_data_factory(num_items=5)

        assert "merchant_name" in receipt
        assert "total_amount" in receipt
        assert len(receipt["line_items"]) == 5

    def test_mock_openai_response_structure(self, mock_openai_success_response):
        """Verify OpenAI mock response has correct structure."""
        assert "choices" in mock_openai_success_response
        assert len(mock_openai_success_response["choices"]) > 0
        assert "message" in mock_openai_success_response["choices"][0]
        assert "content" in mock_openai_success_response["choices"][0]["message"]

    def test_mock_ocr_text_not_empty(self, mock_ocr_text):
        """Verify OCR mock returns text."""
        assert len(mock_ocr_text) > 0
        assert "WHOLE FOODS" in mock_ocr_text

    def test_sample_image_bytes_valid(self, sample_image_bytes):
        """Verify sample image is valid PNG."""
        # PNG files start with these magic bytes
        assert sample_image_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    def test_sample_pdf_bytes_valid(self, sample_pdf_bytes):
        """Verify sample PDF is valid."""
        assert sample_pdf_bytes.startswith(b"%PDF-")

    def test_image_quality_fixtures(self, mock_image_quality_high, mock_image_quality_low):
        """Verify quality mock fixtures have correct scores."""
        assert mock_image_quality_high["total_score"] == 4
        assert mock_image_quality_high["recommendation"] == "ocr"

        assert mock_image_quality_low["total_score"] == 1
        assert mock_image_quality_low["recommendation"] == "vision"

    def test_receipt_validator(self, assert_valid_receipt, sample_receipt_data):
        """Verify receipt validator works."""
        # Should not raise
        assert_valid_receipt(sample_receipt_data)

    def test_receipt_validator_catches_invalid(self, assert_valid_receipt):
        """Verify receipt validator catches missing fields."""
        with pytest.raises(AssertionError):
            assert_valid_receipt({})  # Missing required fields

    @pytest.mark.unit
    def test_marker_unit(self):
        """Verify unit marker works."""
        assert True

    @pytest.mark.integration
    def test_marker_integration(self):
        """Verify integration marker works."""
        assert True

    @pytest.mark.api
    def test_marker_api(self):
        """Verify api marker works."""
        assert True
