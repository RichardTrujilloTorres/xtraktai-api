# 🏗️ Receipt API - Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT APPLICATION                        │
│                    (Web / Mobile / Desktop)                      │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ HTTP POST /process-receipt
                                │ (multipart/form-data)
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                         RECEIPT API                              │
│                      (FastAPI Container)                         │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                     app/main.py                        │    │
│  │              (FastAPI Application)                     │    │
│  │                                                        │    │
│  │  • POST /process-receipt  → Process receipt file      │    │
│  │  • GET  /health          → Health check               │    │
│  │  • GET  /docs            → Swagger UI                 │    │
│  └─────────────────┬──────────────────────────────────────┘    │
│                    │                                            │
│                    │ 1. Save uploaded file                      │
│                    │                                            │
│  ┌─────────────────▼──────────────────────────────────────┐    │
│  │                    app/ocr.py                          │    │
│  │              (OCR Text Extraction)                     │    │
│  │                                                        │    │
│  │  • extract_text_from_image()  → Handle JPG/PNG        │    │
│  │  • extract_text_from_pdf()    → Handle PDFs           │    │
│  │  • Uses: Tesseract OCR + pdf2image                    │    │
│  └─────────────────┬──────────────────────────────────────┘    │
│                    │                                            │
│                    │ 2. Raw OCR text                            │
│                    │                                            │
│  ┌─────────────────▼──────────────────────────────────────┐    │
│  │                 app/llm_parser.py                      │    │
│  │            (AI-Powered Data Extraction)                │    │
│  │                                                        │    │
│  │  • parse_receipt_with_llm()   → Extract structured    │    │
│  │  • validate_receipt_data()    → Validate results      │    │
│  │  • Uses: OpenAI GPT-4o-mini                           │    │
│  └─────────────────┬──────────────────────────────────────┘    │
│                    │                                            │
│                    │ 3. Parsed data (dict)                      │
│                    │                                            │
│  ┌─────────────────▼──────────────────────────────────────┐    │
│  │                  app/schemas.py                        │    │
│  │              (Pydantic Validation)                     │    │
│  │                                                        │    │
│  │  • ReceiptData        → Main receipt model            │    │
│  │  • LineItem           → Individual items              │    │
│  │  • ReceiptMetadata    → Additional metadata           │    │
│  │  • ReceiptResponse    → API response format           │    │
│  └─────────────────┬──────────────────────────────────────┘    │
│                    │                                            │
│                    │ 4. Validated ReceiptResponse               │
│                    │                                            │
└────────────────────┼────────────────────────────────────────────┘
                     │
                     │ JSON Response
                     │
┌────────────────────▼────────────────────────────────────────────┐
│                      CLIENT RECEIVES                            │
│                    Structured Receipt Data                      │
│                         (JSON)                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
Receipt Image/PDF
      │
      ▼
┌─────────────┐
│   Upload    │  → File saved temporarily
└─────┬───────┘
      │
      ▼
┌─────────────┐
│  Tesseract  │  → Extract text using OCR
│     OCR     │     - Handle images (JPG, PNG)
└─────┬───────┘     - Convert PDFs to images
      │
      │ Raw text string
      │
      ▼
┌─────────────┐
│   OpenAI    │  → Parse text with AI
│  GPT-4o-mini│     - Extract structured data
└─────┬───────┘     - Normalize formats
      │
      │ Unvalidated dict
      │
      ▼
┌─────────────┐
│  Pydantic   │  → Validate and serialize
│ Validation  │     - Type checking
└─────┬───────┘     - Required fields
      │
      │ ReceiptResponse object
      │
      ▼
┌─────────────┐
│  JSON API   │  → Return to client
│  Response   │
└─────────────┘
```

---

## Component Interactions

```
┌──────────────┐
│   main.py    │  FastAPI application entry point
└──────┬───────┘
       │
       ├─────► config.py      (Load environment variables)
       │
       ├─────► ocr.py         (Text extraction)
       │       │
       │       └─────► Tesseract (External binary)
       │       └─────► pdf2image (External library)
       │
       ├─────► llm_parser.py  (AI parsing)
       │       │
       │       └─────► OpenAI API (External service)
       │
       ├─────► schemas.py     (Data models)
       │
       └─────► utils.py       (Helper functions)
```

---

## Technology Stack Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Container                      │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Python 3.11 Runtime                  │  │
│  │                                                   │  │
│  │  ┌─────────────────────────────────────────────┐ │  │
│  │  │          FastAPI Framework                  │ │  │
│  │  │                                             │ │  │
│  │  │  ┌───────────────────────────────────────┐ │ │  │
│  │  │  │         Application Code              │ │ │  │
│  │  │  │                                       │ │ │  │
│  │  │  │  • Request handling                   │ │ │  │
│  │  │  │  • OCR processing (Tesseract)        │ │ │  │
│  │  │  │  • LLM calls (OpenAI)                │ │ │  │
│  │  │  │  • Data validation (Pydantic)        │ │ │  │
│  │  │  └───────────────────────────────────────┘ │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
           │                              │
           │                              │
           ▼                              ▼
┌──────────────────┐          ┌──────────────────┐
│   Tesseract OCR  │          │   OpenAI API     │
│  (System Binary) │          │ (External Cloud) │
└──────────────────┘          └──────────────────┘
```

---

## Processing Pipeline

```
Receipt Upload
     │
     ▼
[File Validation]
     │ ✓ Type check
     │ ✓ Size check
     │
     ▼
[Temporary Storage]
     │
     ▼
[OCR Processing]
     │
     ├─ If PDF ──► [pdf2image] ──► [Tesseract]
     │
     └─ If Image ──► [Tesseract directly]
     │
     ▼
[Raw Text String]
     │
     ▼
[LLM Processing]
     │
     ├─ System prompt (extraction rules)
     ├─ User prompt (OCR text)
     │
     ▼
[OpenAI API Call]
     │
     ▼
[JSON Response]
     │
     ▼
[Parse & Clean]
     │
     ▼
[Pydantic Validation]
     │
     ├─ Type checking
     ├─ Required fields
     ├─ Format validation
     │
     ▼
[Validated Receipt Object]
     │
     ▼
[Serialize to JSON]
     │
     ▼
[HTTP Response]
     │
     ▼
[Clean up temp files]
     │
     ▼
   Done ✓
```

---

## Error Handling Flow

```
Request Received
     │
     ▼
[Input Validation]
     │
     ├─ Invalid file type ──► 400 Bad Request
     ├─ File too large ────► 400 Bad Request
     ├─ Empty file ─────────► 400 Bad Request
     │
     ▼ Valid input
[OCR Processing]
     │
     ├─ OCR fails ──────────► 500 Server Error
     ├─ No text extracted ──► 400 Bad Request
     │
     ▼ Text extracted
[LLM Processing]
     │
     ├─ API key invalid ────► 500 Server Error
     ├─ Rate limit hit ─────► 429 Too Many Requests
     ├─ Invalid JSON ───────► 500 Server Error
     │
     ▼ Parsed successfully
[Validation]
     │
     ├─ Missing required ───► 500 Server Error
     ├─ Invalid format ─────► 500 Server Error
     │
     ▼ All valid
[Success Response] ──────────► 200 OK
     │
     ▼
[Cleanup]
```

---

## Scaling Architecture

```
                        ┌────────────────┐
                        │  Load Balancer │
                        └───────┬────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
         ┌──────────┐    ┌──────────┐    ┌──────────┐
         │ Instance │    │ Instance │    │ Instance │
         │    #1    │    │    #2    │    │    #3    │
         └─────┬────┘    └─────┬────┘    └─────┬────┘
               │               │               │
               └───────────────┼───────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
         ┌─────────────┐              ┌─────────────┐
         │  Tesseract  │              │  OpenAI API │
         │   (Local)   │              │  (External) │
         └─────────────┘              └─────────────┘
```

---

## Security Layers

```
┌─────────────────────────────────────────────────────┐
│                   HTTPS/TLS Layer                    │
│              (Secure Communication)                  │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│              API Authentication                      │
│         (Optional: API Keys, OAuth)                  │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│              Input Validation                        │
│    • File type check                                 │
│    • File size limit                                 │
│    • Content validation                              │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│           Environment Variables                      │
│    • API keys not in code                           │
│    • Secure secrets management                      │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│            Temporary File Cleanup                    │
│    • Auto-delete after processing                   │
│    • No persistent storage                          │
└─────────────────────────────────────────────────────┘
```

---

## Monitoring & Observability

```
                    Receipt API
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │  Logs   │    │ Metrics │    │ Traces  │
    │ (stdout)│    │ (health)│    │  (APM)  │
    └────┬────┘    └────┬────┘    └────┬────┘
         │              │              │
         └──────────────┴──────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │  Monitoring Tool │
              │  (Datadog, etc.) │
              └──────────────────┘
```

---

## File Lifecycle

```
Upload ──► Save ──► Process ──► Respond ──► Delete
  │         │         │           │          │
  ▼         ▼         ▼           ▼          ▼
Start    /tmp     OCR+LLM      JSON      Cleanup
         file                 response   complete
```

---

This architecture is designed to be:
- ✅ **Scalable**: Stateless design, easy to replicate
- ✅ **Secure**: No data persistence, environment-based config
- ✅ **Fast**: Async processing with FastAPI
- ✅ **Maintainable**: Clear separation of concerns
- ✅ **Observable**: Logging and health checks built-in
- ✅ **Containerized**: Easy deployment with Docker
