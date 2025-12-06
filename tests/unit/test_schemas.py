"""
Unit tests for Pydantic schemas
"""
import pytest
from datetime import date
from pydantic import ValidationError


class TestLineItem:
    """Tests for LineItem schema"""

    def test_valid_line_item_all_fields(self):
        """Line item with all fields populated"""
        from app.schemas import LineItem

        item = LineItem(
            description="Organic Bananas",
            quantity=2.5,
            unit_price=0.79,
            total_price=1.98,
            category="Produce",
        )

        assert item.description == "Organic Bananas"
        assert item.quantity == 2.5
        assert item.unit_price == 0.79
        assert item.total_price == 1.98
        assert item.category == "Produce"

    def test_line_item_only_required_fields(self):
        """Line item with only description (required)"""
        from app.schemas import LineItem

        item = LineItem(description="Mystery Item")

        assert item.description == "Mystery Item"
        assert item.quantity is None
        assert item.unit_price is None
        assert item.total_price is None
        assert item.category is None

    def test_line_item_missing_description_fails(self):
        """Line item without description should fail"""
        from app.schemas import LineItem

        with pytest.raises(ValidationError) as exc_info:
            LineItem(quantity=1, unit_price=5.00)

        assert "description" in str(exc_info.value)


class TestReceiptMetadata:
    """Tests for ReceiptMetadata schema"""

    def test_metadata_all_fields(self):
        """Metadata with all optional fields"""
        from app.schemas import ReceiptMetadata

        metadata = ReceiptMetadata(
            store_location="123 Main St",
            store_phone="555-1234",
            payment_method="Credit",
            payment_last_four="1234",
            cashier="John",
            register_number="R01",
            transaction_id="TXN123",
            category="Groceries",
        )

        assert metadata.store_location == "123 Main St"
        assert metadata.payment_method == "Credit"
        assert metadata.category == "Groceries"

    def test_metadata_empty(self):
        """Metadata with no fields (all optional)"""
        from app.schemas import ReceiptMetadata

        metadata = ReceiptMetadata()

        assert metadata.store_location is None
        assert metadata.payment_method is None


class TestReceiptData:
    """Tests for ReceiptData schema"""

    def test_receipt_data_full(self):
        """Receipt with all fields"""
        from app.schemas import ReceiptData, LineItem, ReceiptMetadata

        receipt = ReceiptData(
            merchant_name="Whole Foods",
            receipt_number="12345",
            receipt_date=date(2024, 12, 5),
            receipt_time="14:30",
            subtotal=45.00,
            tax_amount=3.85,
            tip_amount=5.00,
            discount_amount=2.50,
            total_amount=51.35,
            currency="USD",
            extraction_confidence="high",
            line_items=[
                LineItem(description="Bananas", total_price=1.98),
            ],
            metadata=ReceiptMetadata(payment_method="Credit"),
        )

        assert receipt.merchant_name == "Whole Foods"
        assert receipt.total_amount == 51.35
        assert len(receipt.line_items) == 1
        assert receipt.metadata.payment_method == "Credit"

    def test_receipt_data_minimal(self):
        """Receipt with only required field"""
        from app.schemas import ReceiptData

        receipt = ReceiptData(merchant_name="Corner Store")

        assert receipt.merchant_name == "Corner Store"
        assert receipt.currency == "USD"  # default
        assert receipt.line_items == []  # default
        assert receipt.total_amount is None

    def test_receipt_data_missing_merchant_fails(self):
        """Receipt without merchant_name should fail"""
        from app.schemas import ReceiptData

        with pytest.raises(ValidationError) as exc_info:
            ReceiptData(total_amount=50.00)

        assert "merchant_name" in str(exc_info.value)

    def test_receipt_data_date_parsing(self):
        """Receipt date accepts date object"""
        from app.schemas import ReceiptData

        receipt = ReceiptData(
            merchant_name="Store",
            receipt_date=date(2024, 1, 15),
        )

        assert receipt.receipt_date == date(2024, 1, 15)

    def test_receipt_data_currency_default(self):
        """Currency defaults to USD"""
        from app.schemas import ReceiptData

        receipt = ReceiptData(merchant_name="Store")
        assert receipt.currency == "USD"

    def test_receipt_data_different_currency(self):
        """Currency can be set to other values"""
        from app.schemas import ReceiptData

        receipt = ReceiptData(merchant_name="Store", currency="EUR")
        assert receipt.currency == "EUR"


class TestReceiptResponse:
    """Tests for ReceiptResponse schema"""

    def test_receipt_response(self):
        """Valid receipt response"""
        from app.schemas import ReceiptResponse, ReceiptData

        response = ReceiptResponse(
            status="success",
            data=ReceiptData(merchant_name="Store", total_amount=25.99),
            raw_text="STORE\nTOTAL $25.99",
        )

        assert response.status == "success"
        assert response.data.merchant_name == "Store"
        assert response.raw_text is not None

    def test_receipt_response_without_raw_text(self):
        """Receipt response without optional raw_text"""
        from app.schemas import ReceiptResponse, ReceiptData

        response = ReceiptResponse(
            status="success",
            data=ReceiptData(merchant_name="Store"),
        )

        assert response.raw_text is None


class TestErrorResponse:
    """Tests for ErrorResponse schema"""

    def test_error_response(self):
        """Valid error response"""
        from app.schemas import ErrorResponse

        error = ErrorResponse(message="File too large")

        assert error.status == "error"  # default
        assert error.message == "File too large"

    def test_error_response_custom_status(self):
        """Error response with custom status"""
        from app.schemas import ErrorResponse

        error = ErrorResponse(status="failed", message="Invalid format")

        assert error.status == "failed"
        assert error.message == "Invalid format"
