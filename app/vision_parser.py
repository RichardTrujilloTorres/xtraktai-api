"""
Vision-based receipt parser using OpenAI GPT-4 Vision
This bypasses OCR entirely and reads images directly
"""
import base64
from openai import OpenAI
import json
import os
from app.config import settings
from app.schemas import ReceiptData


def encode_image_to_base64(image_path: str) -> str:
    """
    Encode image file to base64 string

    Args:
        image_path: Path to image file

    Returns:
        Base64 encoded string
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def parse_receipt_with_vision(image_path: str) -> ReceiptData:
    """
    Parse receipt using GPT-4 Vision (no OCR needed!)

    Args:
        image_path: Path to receipt image

    Returns:
        ReceiptData object with structured information
    """
    # Initialize OpenAI client
    os.environ['OPENAI_API_KEY'] = settings.OPENAI_API_KEY
    client = OpenAI()

    # Encode image
    base64_image = encode_image_to_base64(image_path)

    # Determine image type
    if image_path.lower().endswith('.png'):
        media_type = "image/png"
    elif image_path.lower().endswith(('.jpg', '.jpeg')):
        media_type = "image/jpeg"
    else:
        media_type = "image/jpeg"

    # Vision API prompt
    system_prompt = """You are an expert at reading receipts and extracting structured data.
Analyze the receipt image carefully and extract ALL information you can see.

CRITICAL: Look very carefully at numbers - don't miss digits!
For amounts like "33.04", make sure you see BOTH 3's, not just "3.04".

Return ONLY valid JSON with no markdown formatting, no code blocks, no additional text.

Extract these fields:
- merchant_name: Store/business name
- receipt_number: Receipt or transaction number
- receipt_date: Date in YYYY-MM-DD format (if you see format like DD-MM-YYYY, convert it)
- receipt_time: Time in HH:MM format (24-hour)
- subtotal: Amount before tax
- tax_amount: Tax amount (or sum of all IVA/VAT if multiple)
- tip_amount: Tip if present
- discount_amount: Any discounts (SCONTO)
- total_amount: TOTAL/TOTALE amount (CRITICAL: read this very carefully!)
- currency: EUR for European receipts, USD otherwise
- extraction_confidence: "high" if image is clear, "medium" if some parts unclear, "low" if very faded
- line_items: Array of items with:
  - description: Item name
  - quantity: Quantity if shown
  - unit_price: Price per unit if shown
  - total_price: Total for this item if shown
  - category: Guess category (Groceries, Produce, Dairy, etc.)
- metadata:
  - store_location: Store address if visible
  - store_phone: Phone number if visible
  - payment_method: Cash/Credit/Debit (look for CARTA, CONTANTI, etc.)
  - payment_last_four: Last 4 digits if visible
  - cashier: Cashier name/ID if visible
  - register_number: Register number if visible
  - transaction_id: Transaction ID if visible
  - category: Overall category (Groceries, Dining, Retail, Gas, etc.)

If you can't read a field clearly, use null. But TRY HARD to read the total amount correctly!
"""

    try:
        # Call Vision API
        response = client.chat.completions.create(
            model="gpt-4o",  # GPT-4 Vision
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": system_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{base64_image}",
                                "detail": "high"  # High detail for better accuracy
                            }
                        }
                    ]
                }
            ],
            temperature=0.0,
            max_tokens=2000
        )

        # Extract and parse JSON
        raw_response = response.choices[0].message.content.strip()

        # Clean up response
        if raw_response.startswith("```json"):
            raw_response = raw_response.replace("```json", "", 1)
        if raw_response.startswith("```"):
            raw_response = raw_response.replace("```", "", 1)
        if raw_response.endswith("```"):
            raw_response = raw_response.rsplit("```", 1)[0]

        raw_response = raw_response.strip()

        # Parse JSON
        parsed_data = json.loads(raw_response)

        # Convert to Pydantic model
        receipt_data = ReceiptData(**parsed_data)

        return receipt_data

    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse Vision API response as JSON: {str(e)}\nResponse: {raw_response}")
    except Exception as e:
        raise Exception(f"Error parsing receipt with Vision API: {str(e)}")


def parse_receipt_with_vision_fallback(image_path: str, ocr_text: str = None) -> ReceiptData:
    """
    Parse receipt with Vision API, using OCR text as fallback

    Args:
        image_path: Path to receipt image
        ocr_text: Optional pre-extracted OCR text

    Returns:
        ReceiptData object
    """
    try:
        # Try Vision API first
        return parse_receipt_with_vision(image_path)
    except Exception as vision_error:
        print(f"Vision API failed: {vision_error}")

        # Fallback to OCR + text-based LLM
        if ocr_text:
            from app.llm_parser import parse_receipt_with_llm
            return parse_receipt_with_llm(ocr_text)
        else:
            raise vision_error