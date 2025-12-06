# Test Fixtures

This directory contains static test fixtures.

## Structure

```
fixtures/
├── images/           # Sample receipt images for testing
│   ├── good_receipt.png
│   ├── blurry_receipt.png
│   └── receipt.pdf
└── responses/        # Mock API responses
    ├── openai_success.json
    └── ocr_output.txt
```

## Note

Most fixtures are generated dynamically in `conftest.py`.
Add static files here only when needed for specific test cases.
