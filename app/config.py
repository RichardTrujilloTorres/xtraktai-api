"""
Configuration settings for the Receipt Processing API
Loads environment variables and defines application settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # OpenAI Configuration
    OPENAI_API_KEY: str
    MODEL_NAME: str = "gpt-4o-mini"

    # Processing Method
    USE_VISION_API: bool = True  # Use Vision API by default (better for receipts!)
    USE_SMART_ROUTING: bool = False  # Auto-choose based on image quality (future: Phase 2)

    # Application Settings
    INCLUDE_RAW_TEXT: bool = False  # Whether to include raw OCR text in response
    MAX_FILE_SIZE_MB: int = 10

    # OCR Settings
    TESSERACT_CMD: Optional[str] = None  # Path to tesseract executable if not in PATH

    class Config:
        env_file = ".env"
        case_sensitive = True


# Initialize settings
settings = Settings()

# Configure Tesseract path if specified
if settings.TESSERACT_CMD:
    import pytesseract

    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD