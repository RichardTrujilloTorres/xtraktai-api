"""
OCR module for extracting text from receipt images and PDFs
Uses Tesseract OCR and pdf2image with image enhancement
"""
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from pdf2image import convert_from_path
import os
from pathlib import Path


def preprocess_image(image):
    """
    Preprocess image for better OCR results

    Args:
        image: PIL Image object

    Returns:
        Enhanced PIL Image
    """
    # Convert to grayscale if not already
    if image.mode != 'L':
        image = image.convert('L')

    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)

    # Increase sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.5)

    # Auto contrast
    image = ImageOps.autocontrast(image, cutoff=2)

    return image


def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from an image file using Tesseract OCR

    Args:
        image_path: Path to the image file

    Returns:
        Extracted text as string
    """
    try:
        image = Image.open(image_path)

        # Preprocess image for better OCR
        enhanced_image = preprocess_image(image)

        # Tesseract configuration for better receipt recognition
        # --oem 3: Use default OCR Engine Mode
        # --psm 6: Assume a single uniform block of text
        custom_config = r'--oem 3 --psm 6'

        text = pytesseract.image_to_string(enhanced_image, config=custom_config)
        return text.strip()

    except Exception as e:
        raise Exception(f"Error extracting text from image: {str(e)}")


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file by converting to images first

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text as string
    """
    try:
        # Convert PDF pages to images
        images = convert_from_path(pdf_path, dpi=300)

        all_text = []

        # Process each page
        for i, image in enumerate(images):
            # Preprocess for better OCR
            enhanced_image = preprocess_image(image)

            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(enhanced_image, config=custom_config)
            all_text.append(text.strip())

        # Combine all pages
        combined_text = "\n\n--- PAGE BREAK ---\n\n".join(all_text)
        return combined_text.strip()

    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from a file (auto-detect PDF or image)

    Args:
        file_path: Path to the receipt file

    Returns:
        Extracted text as string
    """
    file_ext = Path(file_path).suffix.lower()

    if file_ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_ext in ['.png', '.jpg', '.jpeg']:
        return extract_text_from_image(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")


def preprocess_text(text: str) -> str:
    """
    Clean and preprocess extracted text

    Args:
        text: Raw OCR text

    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    cleaned_text = '\n'.join(lines)

    return cleaned_text