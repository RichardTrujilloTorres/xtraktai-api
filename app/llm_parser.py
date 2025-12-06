"""
LLM Parser for extracting structured data from receipt text
Uses OpenAI GPT models
"""
from openai import OpenAI
import json
from datetime import datetime
from app.config import settings
from app.schemas import ReceiptData, LineItem, ReceiptMetadata


def parse_receipt_with_llm(ocr_text: str) -> ReceiptData:
    """
    Parse OCR text using OpenAI LLM to extract structured receipt data

    Args:
        ocr_text: Raw text extracted from receipt via OCR

    Returns:
        ReceiptData object with structured information
    """
    # Initialize OpenAI client - let it use default HTTP client
    import os
    os.environ['OPENAI_API_KEY'] = settings.OPENAI_API_KEY
    client = OpenAI()

    # Define the extraction prompt
    system_prompt = """You are an AI assistant specialized in extracting structured data from receipts.
Your task is to analyze receipt text and extract key information into a structured JSON format.

IMPORTANT: Return ONLY valid JSON with no markdown formatting, no code blocks, no additional text.

Extract the following information:
- merchant_name (required): The store or business name
- receipt_number: Receipt or transaction number
- receipt_date: Date in YYYY-MM-DD format
- receipt_time: Time in HH:MM format (24-hour)
- subtotal: Amount before tax
- tax_amount: Tax amount
- tip_amount: Tip if present
- discount_amount: Any discounts applied
- total_amount: Final total amount (IMPORTANT: Try your best to find this even if unclear)
- currency: Currency code (default: USD, use EUR for European receipts)
- extraction_confidence: "high", "medium", or "low" based on text quality
- line_items: Array of purchased items with:
  - description (required)
  - quantity
  - unit_price
  - total_price
  - category (e.g., Food, Beverage, Electronics)
- metadata:
  - store_location: Store address
  - store_phone: Phone number
  - payment_method: Cash, Credit, Debit, etc.
  - payment_last_four: Last 4 digits of card
  - cashier: Cashier name or ID
  - register_number: Register/terminal number
  - transaction_id: Transaction ID
  - category: Overall category (Groceries, Dining, Retail, Gas, etc.)

If a field cannot be determined, use null. For amounts, use float numbers without currency symbols.
If the text is unclear or faded, still try to extract what you can and set extraction_confidence to "low".
"""

    user_prompt = f"""Extract structured data from this receipt text:

{ocr_text}

Return the data as a JSON object matching the schema described."""

    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,  # Deterministic output
            max_tokens=2000
        )

        # Extract and parse the JSON response
        raw_response = response.choices[0].message.content.strip()

        # Clean up the response (remove markdown code blocks if present)
        if raw_response.startswith("```json"):
            raw_response = raw_response.replace("```json", "", 1)
        if raw_response.startswith("```"):
            raw_response = raw_response.replace("```", "", 1)
        if raw_response.endswith("```"):
            raw_response = raw_response.rsplit("```", 1)[0]

        raw_response = raw_response.strip()

        # Parse JSON
        parsed_data = json.loads(raw_response)

        # Convert to Pydantic model (validates and normalizes)
        receipt_data = ReceiptData(**parsed_data)

        return receipt_data

    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse LLM response as JSON: {str(e)}\nResponse: {raw_response}")
    except Exception as e:
        raise Exception(f"Error parsing receipt with LLM: {str(e)}")


def validate_receipt_data(receipt_data: ReceiptData) -> bool:
    """
    Perform additional validation on extracted receipt data

    Args:
        receipt_data: Parsed receipt data

    Returns:
        True if valid, raises exception otherwise
    """
    # Check required fields
    if not receipt_data.merchant_name:
        raise ValueError("merchant_name is required")

    if receipt_data.total_amount is None or receipt_data.total_amount < 0:
        raise ValueError("total_amount must be a positive number")

    # Validate amounts add up (if all present)
    if all([
        receipt_data.subtotal is not None,
        receipt_data.tax_amount is not None,
        receipt_data.tip_amount is not None,
        receipt_data.discount_amount is not None
    ]):
        calculated_total = (
                receipt_data.subtotal +
                receipt_data.tax_amount +
                (receipt_data.tip_amount or 0) -
                (receipt_data.discount_amount or 0)
        )

        # Allow for small rounding differences
        if abs(calculated_total - receipt_data.total_amount) > 0.10:
            # Just warn, don't fail
            print(
                f"Warning: Calculated total ({calculated_total}) doesn't match stated total ({receipt_data.total_amount})")

    return True