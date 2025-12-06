"""
Pydantic schemas for receipt data validation and serialization
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class LineItem(BaseModel):
    """Individual item on the receipt"""
    description: str = Field(..., description="Item name or description")
    quantity: Optional[float] = Field(None, description="Quantity purchased")
    unit_price: Optional[float] = Field(None, description="Price per unit")
    total_price: Optional[float] = Field(None, description="Total price for this line item")
    category: Optional[str] = Field(None, description="Item category (e.g., Food, Beverage, Electronics)")


class ReceiptMetadata(BaseModel):
    """Additional metadata about the receipt"""
    store_location: Optional[str] = Field(None, description="Store address or location")
    store_phone: Optional[str] = Field(None, description="Store phone number")
    payment_method: Optional[str] = Field(None, description="Payment method (Cash, Credit, Debit, etc.)")
    payment_last_four: Optional[str] = Field(None, description="Last 4 digits of card if applicable")
    cashier: Optional[str] = Field(None, description="Cashier name or ID")
    register_number: Optional[str] = Field(None, description="Register or terminal number")
    transaction_id: Optional[str] = Field(None, description="Transaction or reference ID")
    category: Optional[str] = Field(None, description="Receipt category (Groceries, Dining, Retail, etc.)")


class ReceiptData(BaseModel):
    """Structured receipt data"""
    merchant_name: str = Field(..., description="Name of the merchant/store")
    receipt_number: Optional[str] = Field(None, description="Receipt or transaction number")
    receipt_date: Optional[date] = Field(None, description="Date of purchase")
    receipt_time: Optional[str] = Field(None, description="Time of purchase")
    subtotal: Optional[float] = Field(None, description="Subtotal before tax")
    tax_amount: Optional[float] = Field(None, description="Total tax amount")
    tip_amount: Optional[float] = Field(None, description="Tip amount if applicable")
    discount_amount: Optional[float] = Field(None, description="Total discount amount")
    total_amount: Optional[float] = Field(None, description="Final total amount")
    currency: str = Field(default="USD", description="Currency code (USD, EUR, etc.)")
    extraction_confidence: Optional[str] = Field(None, description="Confidence level: high, medium, low")
    line_items: Optional[List[LineItem]] = Field(default=[], description="List of purchased items")
    metadata: Optional[ReceiptMetadata] = Field(default=None, description="Additional receipt metadata")


class ReceiptResponse(BaseModel):
    """API response for receipt processing"""
    status: str = Field(..., description="Response status")
    data: ReceiptData = Field(..., description="Extracted receipt data")
    raw_text: Optional[str] = Field(None, description="Raw OCR text (if enabled)")


class ErrorResponse(BaseModel):
    """API error response"""
    status: str = Field(default="error", description="Status indicator")
    message: str = Field(..., description="Error message")