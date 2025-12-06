# Receipt Processing API - Project Overview

## 📋 Summary

This project is a receipt processing microservice built using the same architecture as the nvola-api invoice processor, but adapted specifically for receipts.

## 🔄 Key Differences from nvola-api (Invoice Processor)

### Data Model Changes

| Invoice Field | Receipt Field | Notes |
|--------------|---------------|-------|
| `vendor_name` | `merchant_name` | More appropriate for retail/restaurants |
| `invoice_number` | `receipt_number` | Receipts use different numbering |
| `invoice_date` | `receipt_date` + `receipt_time` | Receipts often include time |
| `due_date` | ❌ Removed | Not applicable for receipts |
| `payment_terms` | ❌ Removed | Not applicable for receipts |
| ❌ Not present | `tip_amount` | Common in restaurant receipts |
| ❌ Not present | `discount_amount` | Common in retail receipts |
| ❌ Not present | `payment_method` | Important for expense tracking |
| ❌ Not present | `store_location` | Useful metadata |
| ❌ Not present | `cashier` | Often present on receipts |

### Additional Receipt-Specific Features

1. **Time Tracking**: Receipts include `receipt_time` field
2. **Payment Information**: 
   - `payment_method` (Cash, Credit, Debit)
   - `payment_last_four` (last 4 digits of card)
3. **Store Metadata**:
   - `store_location`
   - `store_phone`
   - `register_number`
   - `cashier`
4. **Enhanced Line Items**: Each item can have a `category` field
5. **Receipt Categories**: Overall categorization (Groceries, Dining, Retail, etc.)

### Schema Comparison

#### Invoice Schema (nvola-api)
```python
{
  "vendor_name": str,
  "invoice_number": str,
  "invoice_date": date,
  "due_date": date,
  "total_amount": float,
  "currency": str,
  "tax_amount": float,
  "line_items": [...],
  "metadata": {
    "category": str,
    "country": str,
    "payment_terms": str
  }
}
```

#### Receipt Schema (this project)
```python
{
  "merchant_name": str,
  "receipt_number": str,
  "receipt_date": date,
  "receipt_time": str,
  "subtotal": float,
  "tax_amount": float,
  "tip_amount": float,
  "discount_amount": float,
  "total_amount": float,
  "currency": str,
  "line_items": [
    {
      "description": str,
      "quantity": float,
      "unit_price": float,
      "total_price": float,
      "category": str  # NEW
    }
  ],
  "metadata": {
    "store_location": str,  # NEW
    "store_phone": str,  # NEW
    "payment_method": str,  # NEW
    "payment_last_four": str,  # NEW
    "cashier": str,  # NEW
    "register_number": str,  # NEW
    "transaction_id": str,  # NEW
    "category": str
  }
}
```

## 📁 Project Structure

```
receipt-api/
├── app/
│   ├── __init__.py         # Package initialization
│   ├── main.py             # FastAPI app with endpoints
│   ├── ocr.py              # Tesseract OCR integration
│   ├── llm_parser.py       # OpenAI GPT parsing
│   ├── schemas.py          # Pydantic models
│   ├── config.py           # Settings & env vars
│   └── utils.py            # Helper functions
├── Dockerfile              # Docker container
├── docker-compose.yaml     # Docker orchestration
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── .gitignore             # Git ignore rules
├── test_api.py            # Testing script
└── README.md              # Documentation
```

## 🔧 Technical Stack

- **Python 3.11**: Modern Python with type hints
- **FastAPI**: High-performance async web framework
- **Pydantic**: Data validation and settings
- **OpenAI GPT-4o-mini**: Natural language processing
- **Tesseract OCR**: Text extraction from images
- **pdf2image**: PDF to image conversion
- **Docker**: Containerization for deployment

## 🚀 Deployment Options

### Option 1: Docker (Recommended)
```bash
docker-compose up --build
```

### Option 2: Local Development
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Option 3: Production (Docker)
```bash
docker build -t receipt-api:latest .
docker run -d -p 8000:8000 --env-file .env receipt-api:latest
```

## 🎯 Use Cases

1. **Expense Tracking Apps**
   - Employees scan receipts for reimbursement
   - Automatic categorization and data entry

2. **Accounting Software**
   - Small business receipt management
   - Tax preparation and record keeping

3. **Personal Finance Apps**
   - Budget tracking
   - Spending analysis

4. **E-commerce Returns**
   - Process return receipts
   - Validate purchase information

5. **Warranty Management**
   - Store receipt data for warranty claims
   - Track purchase dates and amounts

## 🔐 Security Best Practices

1. **API Key Management**
   - Store OpenAI API key in environment variables
   - Never commit `.env` to version control
   - Use secrets management in production

2. **File Upload Security**
   - Validate file types and sizes
   - Scan for malware in production
   - Clean up temporary files immediately

3. **Rate Limiting**
   - Implement rate limiting to prevent abuse
   - Monitor API usage and costs

4. **Authentication** (if public-facing)
   - Add API key authentication
   - Implement user accounts if needed
   - Log all requests for audit trail

## 📊 Performance Considerations

- **OCR Processing**: 2-5 seconds per image
- **LLM Parsing**: 1-3 seconds per receipt
- **Total Time**: ~3-8 seconds per receipt
- **Concurrent Requests**: FastAPI handles async well
- **Cost**: ~$0.001-0.003 per receipt (GPT-4o-mini)

## 🧪 Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test with sample receipt
python test_api.py path/to/receipt.jpg

# Interactive API docs
open http://localhost:8000/docs
```

## 🔄 Integration Example (Python)

```python
import requests

def process_receipt(file_path):
    with open(file_path, 'rb') as f:
        response = requests.post(
            'http://localhost:8000/process-receipt',
            files={'file': f}
        )
    return response.json()

# Use it
result = process_receipt('receipt.jpg')
print(f"Total: ${result['data']['total_amount']}")
print(f"Merchant: {result['data']['merchant_name']}")
```

## 🔄 Integration Example (JavaScript)

```javascript
async function processReceipt(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/process-receipt', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
}
```

## 📈 Future Enhancements

1. **Batch Processing**: Process multiple receipts at once
2. **Multi-language**: Support receipts in different languages
3. **Receipt Validation**: Detect fake or manipulated receipts
4. **Database Storage**: Store processed receipts
5. **Advanced Analytics**: Spending patterns and insights
6. **Mobile SDK**: Native mobile integration
7. **Receipt Templates**: Learn common formats for faster processing

## 🆚 When to Use Invoice vs Receipt API

### Use Invoice API (nvola-api) for:
- B2B transactions
- Formal billing documents
- Payment terms tracking
- Due date management
- Vendor management

### Use Receipt API (this project) for:
- B2C retail transactions
- Restaurant/dining receipts
- Expense reimbursement
- Personal finance tracking
- Quick purchase records

## 📞 Support & Maintenance

- **Dependencies**: Update regularly for security
- **OpenAI API**: Monitor for model updates and deprecations
- **Tesseract**: Keep OCR engine updated
- **Docker Images**: Rebuild periodically with latest base images

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [OpenAI API Guide](https://platform.openai.com/docs/)
- [Tesseract OCR Wiki](https://github.com/tesseract-ocr/tesseract/wiki)

---

**Ready to process receipts? Start with:**
```bash
cd receipt-api
cp .env.example .env
# Add your OpenAI API key to .env
docker-compose up --build
```
