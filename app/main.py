"""
Receipt Processing API - Main Application
FastAPI microservice for processing receipt files using OCR, Vision API, and LLM
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
import tempfile
import os
from pathlib import Path

from app.ocr import extract_text_from_file
from app.llm_parser import parse_receipt_with_llm
from app.vision_parser import parse_receipt_with_vision
from app.quality_check import check_image_quality, should_use_vision_api
from app.schemas import ReceiptResponse, ErrorResponse
from app.config import settings

app = FastAPI(
    title="Receipt Processing API",
    description="AI-powered receipt extraction microservice using OCR and LLM",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Receipt Processing API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "ocr": "tesseract available",
        "llm": "openai configured" if settings.OPENAI_API_KEY else "not configured",
        "vision_api": "enabled" if settings.USE_VISION_API else "disabled"
    }


@app.post("/check-quality")
async def check_receipt_quality(file: UploadFile = File(...)):
    """
    Check receipt image quality without processing
    Useful for pre-upload validation

    Args:
        file: Receipt file to check

    Returns:
        Quality metrics and recommendations
    """
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    try:
        # Save temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            # Only for images, not PDFs
            if file_ext in ['.png', '.jpg', '.jpeg']:
                quality_metrics = check_image_quality(tmp_file_path)

                return {
                    "status": "success",
                    "quality": quality_metrics,
                    "recommended_method": "vision_api" if should_use_vision_api(quality_metrics) else "ocr"
                }
            else:
                return {
                    "status": "success",
                    "message": "Quality check not available for PDFs",
                    "recommended_method": "ocr"
                }
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking quality: {str(e)}"
        )


@app.post("/process-receipt", response_model=ReceiptResponse)
async def process_receipt(
        file: UploadFile = File(...),
        skip_quality_check: bool = Query(False, description="Skip quality validation (not recommended)")
):
    """
    Process a receipt file (PDF, PNG, JPG, JPEG) and extract structured data

    Args:
        file: Receipt file to process
        skip_quality_check: Set to true to skip quality validation

    Returns:
        ReceiptResponse with structured receipt data
    """
    # Validate file type
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            # Optional: Check image quality first (for images only)
            quality_metrics = None
            if not skip_quality_check and file_ext in ['.png', '.jpg', '.jpeg']:
                try:
                    quality_metrics = check_image_quality(tmp_file_path)

                    # Reject if quality is too poor (score < 2)
                    if quality_metrics['quality_score'] < 2:
                        return JSONResponse(
                            status_code=422,
                            content={
                                "status": "quality_too_low",
                                "message": "Image quality too low for reliable processing",
                                "quality_level": quality_metrics['quality_level'],
                                "quality_score": f"{quality_metrics['quality_score']}/4",
                                "recommendations": quality_metrics['recommendations']
                            }
                        )
                except Exception as quality_error:
                    # Don't fail the whole request if quality check fails
                    print(f"Quality check failed: {quality_error}")

            # Choose processing method based on config OR quality
            if quality_metrics and hasattr(settings, 'USE_SMART_ROUTING') and settings.USE_SMART_ROUTING:
                # Smart routing: use quality metrics to decide
                use_vision = should_use_vision_api(quality_metrics)
            else:
                # Use config setting
                use_vision = getattr(settings, 'USE_VISION_API', True)

            if use_vision:
                # Method 1: Vision API (direct image analysis - BEST for receipts!)
                try:
                    receipt_data = parse_receipt_with_vision(tmp_file_path)

                    return ReceiptResponse(
                        status="success",
                        data=receipt_data,
                        raw_text=None  # Vision API doesn't use OCR
                    )
                except Exception as vision_error:
                    print(f"Vision API failed, falling back to OCR: {vision_error}")
                    # Fall through to OCR method

            # Method 2: Traditional OCR + LLM (fallback)
            # Step 1: Extract text using OCR
            extracted_text = extract_text_from_file(tmp_file_path)

            if not extracted_text or len(extracted_text.strip()) < 10:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "message": "Could not extract sufficient text from receipt. Image may be unclear or empty."
                    }
                )

            # Step 2: Parse with LLM
            try:
                receipt_data = parse_receipt_with_llm(extracted_text)

                # Check if we got minimal viable data
                if not receipt_data.merchant_name or receipt_data.merchant_name == "":
                    return JSONResponse(
                        status_code=422,
                        content={
                            "status": "partial_failure",
                            "message": "Receipt text extracted but could not identify merchant. Image quality may be too low.",
                            "raw_text": extracted_text if settings.INCLUDE_RAW_TEXT else "Enable INCLUDE_RAW_TEXT to see extracted text",
                            "suggestion": "Please provide a clearer image or manually enter the receipt data."
                        }
                    )

                # Return success with confidence indicator
                return ReceiptResponse(
                    status="success",
                    data=receipt_data,
                    raw_text=extracted_text if settings.INCLUDE_RAW_TEXT else None
                )

            except Exception as llm_error:
                # If LLM parsing fails, return partial data with OCR text
                return JSONResponse(
                    status_code=422,
                    content={
                        "status": "partial_failure",
                        "message": f"Receipt text extracted but parsing failed: {str(llm_error)}",
                        "raw_text": extracted_text if settings.INCLUDE_RAW_TEXT else "Enable INCLUDE_RAW_TEXT to see extracted text",
                        "suggestion": "Image quality may be too low. Try a clearer photo or re-scan."
                    }
                )

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing receipt: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            status="error",
            message=str(exc)
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)