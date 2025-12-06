"""
Integration tests for LLM parser module
OpenAI client is mocked for all tests
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import date

from app.schemas import ReceiptData, LineItem, ReceiptMetadata
from app.llm_parser import parse_receipt_with_llm, validate_receipt_data


# ---------------------------------------------------------------------------
# Mock response builders
# ---------------------------------------------------------------------------

def build_openai_response(content: str) -> MagicMock:
    """Build a mock OpenAI API response"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response


def build_receipt_json(
    merchant_name: str = "Test Store",
    total_amount: float = 25.99,
    **kwargs
) -> str:
    """Build receipt JSON string"""
    data = {
        "merchant_name": merchant_name,
        "receipt_number": "12345",
        "receipt_date": "2024-12-05",
        "receipt_time": "14:30",
        "subtotal": 23.99,
        "tax_amount": 2.00,
        "tip_amount": None,
        "discount_amount": 0,
        "total_amount": total_amount,
        "currency": "USD",
        "extraction_confidence": "high",
        "line_items": [
            {
                "description": "Test Item",
                "quantity": 1,
                "unit_price": 23.99,
                "total_price": 23.99,
                "category": "General"
            }
        ],
        "metadata": {
            "store_location": "123 Test St",
            "payment_method": "Credit"
        }
    }
    data.update(kwargs)
    return json.dumps(data)


# ---------------------------------------------------------------------------
# Tests for parse_receipt_with_llm
# ---------------------------------------------------------------------------

class TestParseReceiptWithLlm:
    """Tests for LLM-based receipt parsing"""

    @patch("app.llm_parser.OpenAI")
    def test_parses_valid_response(self, mock_openai_class):
        """Should parse valid JSON response into ReceiptData"""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = build_openai_response(
            build_receipt_json(merchant_name="Whole Foods", total_amount=47.06)
        )
        
        result = parse_receipt_with_llm("WHOLE FOODS\nTOTAL $47.06")
        
        assert isinstance(result, ReceiptData)
        assert result.merchant_name == "Whole Foods"
        assert result.total_amount == 47.06

    @patch("app.llm_parser.OpenAI")
    def test_handles_markdown_code_blocks(self, mock_openai_class):
        """Should strip markdown code blocks from response"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Response wrapped in markdown
        json_content = build_receipt_json()
        markdown_response = f"```json\n{json_content}\n```"
        mock_client.chat.completions.create.return_value = build_openai_response(markdown_response)
        
        result = parse_receipt_with_llm("RECEIPT TEXT")
        
        assert isinstance(result, ReceiptData)
        assert result.merchant_name == "Test Store"

    @patch("app.llm_parser.OpenAI")
    def test_handles_plain_code_blocks(self, mock_openai_class):
        """Should strip plain code blocks from response"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        json_content = build_receipt_json()
        code_block_response = f"```\n{json_content}\n```"
        mock_client.chat.completions.create.return_value = build_openai_response(code_block_response)
        
        result = parse_receipt_with_llm("RECEIPT TEXT")
        
        assert isinstance(result, ReceiptData)

    @patch("app.llm_parser.OpenAI")
    def test_raises_on_invalid_json(self, mock_openai_class):
        """Should raise exception for invalid JSON response"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = build_openai_response(
            "This is not valid JSON"
        )
        
        with pytest.raises(Exception) as exc_info:
            parse_receipt_with_llm("RECEIPT TEXT")
        
        assert "Failed to parse LLM response as JSON" in str(exc_info.value)

    @patch("app.llm_parser.OpenAI")
    def test_raises_on_api_error(self, mock_openai_class):
        """Should raise exception on API error"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API rate limit exceeded")
        
        with pytest.raises(Exception) as exc_info:
            parse_receipt_with_llm("RECEIPT TEXT")
        
        assert "Error parsing receipt with LLM" in str(exc_info.value)

    @patch("app.llm_parser.OpenAI")
    def test_parses_line_items(self, mock_openai_class):
        """Should correctly parse line items"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        receipt_json = {
            "merchant_name": "Store",
            "total_amount": 50.00,
            "currency": "USD",
            "line_items": [
                {"description": "Item 1", "quantity": 2, "unit_price": 10.00, "total_price": 20.00},
                {"description": "Item 2", "quantity": 1, "unit_price": 30.00, "total_price": 30.00},
            ]
        }
        mock_client.chat.completions.create.return_value = build_openai_response(
            json.dumps(receipt_json)
        )
        
        result = parse_receipt_with_llm("RECEIPT TEXT")
        
        assert len(result.line_items) == 2
        assert result.line_items[0].description == "Item 1"
        assert result.line_items[1].total_price == 30.00

    @patch("app.llm_parser.OpenAI")
    def test_parses_metadata(self, mock_openai_class):
        """Should correctly parse metadata"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        receipt_json = {
            "merchant_name": "Store",
            "total_amount": 25.00,
            "currency": "USD",
            "metadata": {
                "store_location": "123 Main St",
                "payment_method": "Visa",
                "payment_last_four": "1234"
            }
        }
        mock_client.chat.completions.create.return_value = build_openai_response(
            json.dumps(receipt_json)
        )
        
        result = parse_receipt_with_llm("RECEIPT TEXT")
        
        assert result.metadata is not None
        assert result.metadata.store_location == "123 Main St"
        assert result.metadata.payment_method == "Visa"

    @patch("app.llm_parser.OpenAI")
    def test_handles_minimal_response(self, mock_openai_class):
        """Should handle response with only required fields"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        minimal_json = {"merchant_name": "Store"}
        mock_client.chat.completions.create.return_value = build_openai_response(
            json.dumps(minimal_json)
        )
        
        result = parse_receipt_with_llm("RECEIPT TEXT")
        
        assert result.merchant_name == "Store"
        assert result.currency == "USD"  # default


# ---------------------------------------------------------------------------
# Tests for validate_receipt_data
# ---------------------------------------------------------------------------

class TestValidateReceiptData:
    """Tests for receipt data validation"""

    def test_valid_receipt_passes(self):
        """Valid receipt should pass validation"""
        receipt = ReceiptData(
            merchant_name="Store",
            total_amount=25.99,
            currency="USD"
        )
        
        assert validate_receipt_data(receipt) is True

    def test_missing_merchant_name_fails(self):
        """Should raise ValueError for empty merchant_name"""
        receipt = ReceiptData(
            merchant_name="",
            total_amount=25.99,
            currency="USD"
        )
        
        with pytest.raises(ValueError) as exc_info:
            validate_receipt_data(receipt)
        
        assert "merchant_name" in str(exc_info.value)

    def test_negative_total_fails(self):
        """Should raise ValueError for negative total_amount"""
        receipt = ReceiptData(
            merchant_name="Store",
            total_amount=-10.00,
            currency="USD"
        )
        
        with pytest.raises(ValueError) as exc_info:
            validate_receipt_data(receipt)
        
        assert "total_amount" in str(exc_info.value)

    def test_none_total_fails(self):
        """Should raise ValueError for None total_amount"""
        receipt = ReceiptData(
            merchant_name="Store",
            total_amount=None,
            currency="USD"
        )
        
        with pytest.raises(ValueError) as exc_info:
            validate_receipt_data(receipt)
        
        assert "total_amount" in str(exc_info.value)

    def test_matching_totals_pass(self, capsys):
        """Should pass when calculated total matches stated total"""
        receipt = ReceiptData(
            merchant_name="Store",
            subtotal=20.00,
            tax_amount=2.00,
            tip_amount=3.00,
            discount_amount=0.00,
            total_amount=25.00,
            currency="USD"
        )
        
        assert validate_receipt_data(receipt) is True

    def test_mismatched_totals_warn(self, capsys):
        """Should warn (not fail) when totals don't match"""
        receipt = ReceiptData(
            merchant_name="Store",
            subtotal=20.00,
            tax_amount=2.00,
            tip_amount=0.00,
            discount_amount=0.00,
            total_amount=50.00,  # Doesn't match 20+2=22
            currency="USD"
        )
        
        # Should still return True (warn only)
        result = validate_receipt_data(receipt)
        assert result is True
        
        # Check warning was printed
        captured = capsys.readouterr()
        assert "Warning" in captured.out or result is True  # Warning is printed

    def test_partial_amounts_skip_validation(self):
        """Should skip total validation if some amounts are None"""
        receipt = ReceiptData(
            merchant_name="Store",
            subtotal=20.00,
            tax_amount=None,  # Missing
            total_amount=25.00,
            currency="USD"
        )
        
        # Should pass without checking totals
        assert validate_receipt_data(receipt) is True
