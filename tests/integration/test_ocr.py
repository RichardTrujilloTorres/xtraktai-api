"""
Integration tests for OCR module
All external dependencies (pytesseract, pdf2image) are mocked
"""
import io
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

from app.ocr import (
    preprocess_image,
    extract_text_from_image,
    extract_text_from_pdf,
    extract_text_from_file,
    preprocess_text,
)


# ---------------------------------------------------------------------------
# Helper to create temp image files
# ---------------------------------------------------------------------------

def create_temp_image(suffix=".png") -> str:
    """Create a temporary image file and return its path"""
    img = Image.new("RGB", (800, 1200), color="white")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        img.save(f, format="PNG" if suffix == ".png" else "JPEG")
        return f.name


def create_temp_pdf() -> str:
    """Create a temporary PDF file and return its path"""
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
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_content)
        return f.name


# ---------------------------------------------------------------------------
# Tests for preprocess_image (no mocking needed - pure PIL operations)
# ---------------------------------------------------------------------------

class TestPreprocessImage:
    """Tests for image preprocessing"""

    def test_converts_rgb_to_grayscale(self):
        """RGB image should be converted to grayscale"""
        img = Image.new("RGB", (100, 100), color="red")
        result = preprocess_image(img)
        assert result.mode == "L"

    def test_grayscale_stays_grayscale(self):
        """Grayscale image should remain grayscale"""
        img = Image.new("L", (100, 100), color=128)
        result = preprocess_image(img)
        assert result.mode == "L"

    def test_output_same_size(self):
        """Preprocessed image should be same size"""
        img = Image.new("RGB", (800, 1200), color="white")
        result = preprocess_image(img)
        assert result.size == (800, 1200)

    def test_returns_pil_image(self):
        """Result should be a PIL Image"""
        img = Image.new("RGB", (100, 100), color="white")
        result = preprocess_image(img)
        assert isinstance(result, Image.Image)


# ---------------------------------------------------------------------------
# Tests for extract_text_from_image (mocked pytesseract)
# ---------------------------------------------------------------------------

class TestExtractTextFromImage:
    """Tests for image text extraction"""

    @patch("app.ocr.pytesseract.image_to_string")
    def test_extracts_text_successfully(self, mock_tesseract):
        """Should return extracted text from image"""
        mock_tesseract.return_value = "WHOLE FOODS\nTOTAL $25.99"
        
        image_path = create_temp_image()
        try:
            result = extract_text_from_image(image_path)
            
            assert "WHOLE FOODS" in result
            assert "TOTAL" in result
            mock_tesseract.assert_called_once()
        finally:
            Path(image_path).unlink()

    @patch("app.ocr.pytesseract.image_to_string")
    def test_strips_whitespace(self, mock_tesseract):
        """Should strip leading/trailing whitespace"""
        mock_tesseract.return_value = "  \n  RECEIPT TEXT  \n  "
        
        image_path = create_temp_image()
        try:
            result = extract_text_from_image(image_path)
            assert result == "RECEIPT TEXT"
        finally:
            Path(image_path).unlink()

    @patch("app.ocr.pytesseract.image_to_string")
    def test_handles_empty_result(self, mock_tesseract):
        """Should handle empty OCR result"""
        mock_tesseract.return_value = ""
        
        image_path = create_temp_image()
        try:
            result = extract_text_from_image(image_path)
            assert result == ""
        finally:
            Path(image_path).unlink()

    @patch("app.ocr.pytesseract.image_to_string")
    def test_uses_custom_config(self, mock_tesseract):
        """Should pass custom tesseract config"""
        mock_tesseract.return_value = "TEXT"
        
        image_path = create_temp_image()
        try:
            extract_text_from_image(image_path)
            
            # Check config was passed
            call_kwargs = mock_tesseract.call_args
            assert "config" in call_kwargs.kwargs or len(call_kwargs.args) > 1
        finally:
            Path(image_path).unlink()

    def test_raises_on_missing_file(self):
        """Should raise exception for missing file"""
        with pytest.raises(Exception) as exc_info:
            extract_text_from_image("/nonexistent/path/image.png")
        
        assert "Error extracting text" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Tests for extract_text_from_pdf (mocked pdf2image and pytesseract)
# ---------------------------------------------------------------------------

class TestExtractTextFromPdf:
    """Tests for PDF text extraction"""

    @patch("app.ocr.pytesseract.image_to_string")
    @patch("app.ocr.convert_from_path")
    def test_extracts_text_from_single_page(self, mock_convert, mock_tesseract):
        """Should extract text from single page PDF"""
        # Mock PDF conversion
        mock_image = Image.new("RGB", (800, 1200), color="white")
        mock_convert.return_value = [mock_image]
        mock_tesseract.return_value = "PAGE 1 TEXT"
        
        pdf_path = create_temp_pdf()
        try:
            result = extract_text_from_pdf(pdf_path)
            
            assert "PAGE 1 TEXT" in result
            mock_convert.assert_called_once()
        finally:
            Path(pdf_path).unlink()

    @patch("app.ocr.pytesseract.image_to_string")
    @patch("app.ocr.convert_from_path")
    def test_extracts_text_from_multiple_pages(self, mock_convert, mock_tesseract):
        """Should extract and combine text from multiple pages"""
        # Mock multi-page PDF
        mock_images = [
            Image.new("RGB", (800, 1200), color="white"),
            Image.new("RGB", (800, 1200), color="white"),
        ]
        mock_convert.return_value = mock_images
        mock_tesseract.side_effect = ["PAGE 1", "PAGE 2"]
        
        pdf_path = create_temp_pdf()
        try:
            result = extract_text_from_pdf(pdf_path)
            
            assert "PAGE 1" in result
            assert "PAGE 2" in result
            assert "PAGE BREAK" in result
        finally:
            Path(pdf_path).unlink()

    @patch("app.ocr.convert_from_path")
    def test_raises_on_conversion_error(self, mock_convert):
        """Should raise exception on PDF conversion error"""
        mock_convert.side_effect = Exception("PDF conversion failed")
        
        pdf_path = create_temp_pdf()
        try:
            with pytest.raises(Exception) as exc_info:
                extract_text_from_pdf(pdf_path)
            
            assert "Error extracting text from PDF" in str(exc_info.value)
        finally:
            Path(pdf_path).unlink()


# ---------------------------------------------------------------------------
# Tests for extract_text_from_file (routes to image or PDF)
# ---------------------------------------------------------------------------

class TestExtractTextFromFile:
    """Tests for unified file extraction"""

    @patch("app.ocr.pytesseract.image_to_string")
    def test_routes_png_to_image_extractor(self, mock_tesseract):
        """PNG files should use image extraction"""
        mock_tesseract.return_value = "IMAGE TEXT"
        
        image_path = create_temp_image(".png")
        try:
            result = extract_text_from_file(image_path)
            assert result == "IMAGE TEXT"
        finally:
            Path(image_path).unlink()

    @patch("app.ocr.pytesseract.image_to_string")
    def test_routes_jpg_to_image_extractor(self, mock_tesseract):
        """JPG files should use image extraction"""
        mock_tesseract.return_value = "IMAGE TEXT"
        
        image_path = create_temp_image(".jpg")
        try:
            result = extract_text_from_file(image_path)
            assert result == "IMAGE TEXT"
        finally:
            Path(image_path).unlink()

    @patch("app.ocr.pytesseract.image_to_string")
    @patch("app.ocr.convert_from_path")
    def test_routes_pdf_to_pdf_extractor(self, mock_convert, mock_tesseract):
        """PDF files should use PDF extraction"""
        mock_convert.return_value = [Image.new("RGB", (800, 1200), "white")]
        mock_tesseract.return_value = "PDF TEXT"
        
        pdf_path = create_temp_pdf()
        try:
            result = extract_text_from_file(pdf_path)
            assert result == "PDF TEXT"
        finally:
            Path(pdf_path).unlink()

    def test_raises_on_unsupported_type(self):
        """Should raise ValueError for unsupported file types"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"text content")
            txt_path = f.name
        
        try:
            with pytest.raises(ValueError) as exc_info:
                extract_text_from_file(txt_path)
            
            assert "Unsupported file type" in str(exc_info.value)
        finally:
            Path(txt_path).unlink()


# ---------------------------------------------------------------------------
# Tests for preprocess_text (pure function)
# ---------------------------------------------------------------------------

class TestPreprocessText:
    """Tests for text preprocessing"""

    def test_removes_empty_lines(self):
        """Should remove empty lines"""
        text = "Line 1\n\n\nLine 2"
        result = preprocess_text(text)
        assert result == "Line 1\nLine 2"

    def test_strips_line_whitespace(self):
        """Should strip whitespace from each line"""
        text = "  Line 1  \n  Line 2  "
        result = preprocess_text(text)
        assert result == "Line 1\nLine 2"

    def test_preserves_content(self):
        """Should preserve actual content"""
        text = "STORE NAME\nTOTAL: $25.99"
        result = preprocess_text(text)
        assert "STORE NAME" in result
        assert "TOTAL: $25.99" in result

    def test_handles_empty_string(self):
        """Should handle empty string"""
        result = preprocess_text("")
        assert result == ""

    def test_handles_whitespace_only(self):
        """Should handle whitespace-only string"""
        result = preprocess_text("   \n\n   ")
        assert result == ""
