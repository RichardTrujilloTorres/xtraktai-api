# 🧾 Receipt Processing API

**AI-powered receipt extraction microservice**  
Built with ❤️ using

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-412991?logo=openai&logoColor=white)](https://openai.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![OCR](https://img.shields.io/badge/OCR-Tesseract-FF6F00?logo=google&logoColor=white)](https://github.com/tesseract-ocr/tesseract)

---

## 🧠 Overview

**Receipt Processing API** is a microservice that processes receipt files (PDFs, images, etc.) using OCR and LLMs to produce clean, normalized JSON output.

Perfect for expense tracking apps, accounting systems, or any application that needs to digitize and structure receipt data.

---

## ⚙️ Tech Stack

| Layer | Technology | Description |
|-------|-----------|-------------|
| 🐍 Backend | **Python 3.11** | Language runtime |
| ⚡ Framework | **FastAPI** | High-performance web framework |
| 🧩 AI / NLP | **OpenAI GPT-4o-mini** | Extracts structured data from text |
| 👁️ OCR | **Tesseract + pdf2image** | Extracts text from PDF/image receipts |
| 🧱 Schema | **Pydantic** | Validates and enforces JSON structure |
| 🐳 Containerization | **Docker** | Easily deployable microservice |

---

## ✨ Features

- 📸 Process receipts from images (PNG, JPG, JPEG) and PDFs
- 🤖 AI-powered data extraction with GPT-4o-mini
- 📊 Structured JSON output with complete receipt details
- 💰 Extract line items, totals, taxes, tips, and discounts
- 🏪 Merchant information and store metadata
- 💳 Payment method detection
- 🌐 Multi-currency support
- 🐳 Docker-ready for easy deployment
- 📚 Auto-generated API documentation

---

## 🧾 Example Output

```json
{
  "status": "success",
  "data": {
    "merchant_name": "Whole Foods Market",
    "receipt_number": "0012-34567-8901",
    "receipt_date": "2024-12-05",
    "receipt_time": "14:32",
    "subtotal": 45.67,
    "tax_amount": 3.89,
    "tip_amount": null,
    "discount_amount": 2.50,
    "total_amount": 47.06,
    "currency": "USD",
    "line_items": [
      {
        "description": "Organic Bananas",
        "quantity": 2.5,
        "unit_price": 0.79,
        "total_price": 1.98,
        "category": "Produce"
      },
      {
        "description": "Almond Milk",
        "quantity": 1,
        "unit_price": 4.99,
        "total_price": 4.99,
        "category": "Dairy"
      }
    ],
    "metadata": {
      "store_location": "123 Main St, San Francisco, CA 94102",
      "store_phone": "(415) 555-0123",
      "payment_method": "Credit Card",
      "payment_last_four": "4242",
      "cashier": "Emma T.",
      "register_number": "3",
      "transaction_id": "TXN-2024-120501432",
      "category": "Groceries"
    }
  }
}
```

---

## 🚀 Quick Start

### 1️⃣ Clone the repo

```bash
git clone https://github.com/yourusername/receipt-api.git
cd receipt-api
```

### 2️⃣ Set up environment

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3️⃣ Build and run (Docker)

```bash
docker-compose up --build
```

### 4️⃣ Test it

```bash
curl -X POST http://localhost:8000/process-receipt \
  -F "file=@your-receipt.pdf"
```

---

## 🧩 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root health check |
| `GET` | `/health` | Detailed health check |
| `POST` | `/process-receipt` | Upload receipt and get structured JSON |
| `GET` | `/docs` | Interactive Swagger UI (auto-generated) |
| `GET` | `/redoc` | Alternate ReDoc documentation |

---

## 🧠 Project Structure

```
receipt-api/
├── app/
│   ├── __init__.py         # Package initialization
│   ├── main.py             # FastAPI application entrypoint
│   ├── ocr.py              # OCR text extraction
│   ├── llm_parser.py       # AI parsing + normalization
│   ├── schemas.py          # Pydantic models
│   ├── config.py           # Environment vars + settings
│   └── utils.py            # Helper functions
├── Dockerfile              # Container definition
├── docker-compose.yaml     # Docker compose configuration
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

---

## 🧰 Environment Variables

Create a `.env` file with the following variables:

```env
# Required
OPENAI_API_KEY=sk-...

# Optional
MODEL_NAME=gpt-4o-mini
INCLUDE_RAW_TEXT=false
MAX_FILE_SIZE_MB=10
```

---

## 📦 Local Development Setup

### Prerequisites

- Python 3.11+
- Tesseract OCR (`brew install tesseract` on macOS, `apt-get install tesseract-ocr` on Linux)
- Poppler (`brew install poppler` on macOS, `apt-get install poppler-utils` on Linux)

### Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload
```

Access the API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🐳 Docker Deployment

### Build and run

```bash
docker-compose up --build
```

### Run in detached mode

```bash
docker-compose up -d
```

### View logs

```bash
docker-compose logs -f
```

### Stop the service

```bash
docker-compose down
```

---

## 🧪 Testing the API

### Using cURL

```bash
# Test health endpoint
curl http://localhost:8000/health

# Process a receipt
curl -X POST http://localhost:8000/process-receipt \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/receipt.jpg"
```

### Using Python

```python
import requests

url = "http://localhost:8000/process-receipt"
files = {"file": open("receipt.jpg", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

### Using JavaScript/Fetch

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/process-receipt', {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

## 📊 Supported Receipt Types

- 🛒 **Grocery receipts** (supermarkets, convenience stores)
- 🍔 **Restaurant receipts** (dining, fast food, cafes)
- ⛽ **Gas station receipts**
- 🛍️ **Retail receipts** (clothing, electronics, general merchandise)
- 🏨 **Hotel receipts**
- 🎫 **Entertainment receipts** (movies, events)
- 💊 **Pharmacy receipts**

---

## 🔧 Configuration Options

### OpenAI Models

You can use different OpenAI models by changing `MODEL_NAME`:

- `gpt-4o-mini` (default, fast and cost-effective)
- `gpt-4o` (more accurate, higher cost)
- `gpt-4-turbo` (good balance)

### OCR Customization

For better OCR results, you can adjust Tesseract settings in `app/ocr.py`:

```python
# For receipts with poor quality
custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,$ '
```

---

## 🚨 Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `400` - Bad request (invalid file type, unreadable receipt)
- `500` - Server error (OCR failure, LLM error)

Example error response:

```json
{
  "status": "error",
  "message": "Could not extract sufficient text from receipt"
}
```

---

## 🔐 Security Considerations

- ⚠️ Store your `OPENAI_API_KEY` securely
- 🚫 Never commit `.env` to version control
- 🔒 Use HTTPS in production
- 🛡️ Implement rate limiting for public APIs
- 🗑️ Temporary files are automatically cleaned up

---

## 📈 Roadmap

- ✅ OCR-based text extraction
- ✅ AI-powered receipt normalization
- ✅ Docker support
- ✅ Health endpoint
- 🔲 Batch processing support
- 🔲 Multi-language receipt support
- 🔲 Receipt validation and fraud detection
- 🔲 Receipt categorization training
- 🔲 Database storage integration
- 🔲 Authentication and API keys

---

## 🤝 Contributing

Pull requests welcome! Use [Conventional Commits](https://www.conventionalcommits.org) for clean commit history:

```bash
feat(api): add batch processing endpoint
fix(ocr): improve text extraction for faded receipts
docs(readme): update installation instructions
```

---

## 📜 License

MIT © 2024 — Receipt Processing API

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [OpenAI](https://openai.com/) - GPT models
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Open source OCR
- Inspired by [nvola-api](https://github.com/RichardTrujilloTorres/nvola-api)

---

Built with 🧠, ☕, and ❤️ for better expense tracking.

**Questions? Issues? → [Open an issue](https://github.com/yourusername/receipt-api/issues)**
