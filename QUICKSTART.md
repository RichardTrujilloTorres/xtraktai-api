# 🚀 Quick Start Guide - Receipt Processing API

## ⚡ 5-Minute Setup

### Prerequisites
- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Step 1: Set Up Environment
```bash
cd receipt-api
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```env
OPENAI_API_KEY=sk-your-key-here
MODEL_NAME=gpt-4o-mini
```

### Step 2: Start the API
```bash
docker-compose up --build
```

Wait for the message: `Uvicorn running on http://0.0.0.0:8000`

### Step 3: Test It
Open http://localhost:8000/docs in your browser for the interactive API documentation.

Or test with cURL:
```bash
curl -X POST http://localhost:8000/process-receipt \
  -F "file=@your-receipt.jpg"
```

## 🎯 What You Get

The API will return structured JSON like this:

```json
{
  "status": "success",
  "data": {
    "merchant_name": "Starbucks",
    "receipt_date": "2024-12-05",
    "total_amount": 12.50,
    "line_items": [
      {
        "description": "Grande Latte",
        "total_price": 5.25
      },
      {
        "description": "Blueberry Muffin",
        "total_price": 3.75
      }
    ],
    "metadata": {
      "payment_method": "Credit Card",
      "category": "Dining"
    }
  }
}
```

## 🔧 Common Issues

### "Connection refused"
- Make sure Docker is running
- Wait a few seconds for the container to start fully

### "OCR failed"
- Ensure the image is clear and not too small
- Try a different image format (JPG, PNG, or PDF)
- Check if the receipt has visible text

### "OpenAI API error"
- Verify your API key is correct in `.env`
- Check your OpenAI account has credits
- Ensure no extra spaces in the API key

## 📚 Next Steps

1. **Read the full documentation**: Check `README.md`
2. **Explore the API**: Visit http://localhost:8000/docs
3. **Test with your receipts**: Upload real receipt images
4. **Integrate into your app**: See `PROJECT_OVERVIEW.md` for examples

## 🛑 Stopping the Service

```bash
docker-compose down
```

## 💡 Tips

- Best results with clear, high-resolution images
- Supported formats: JPG, PNG, PDF
- Maximum file size: 10MB (configurable)
- Processing time: 3-8 seconds per receipt

## 🆘 Need Help?

- Check the logs: `docker-compose logs -f`
- Test health: `curl http://localhost:8000/health`
- Open an issue on GitHub

---

**That's it! You're ready to process receipts with AI. 🎉**
