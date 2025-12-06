# 📊 Invoice API vs Receipt API - Complete Comparison

## 🎯 Overview

This document provides a detailed comparison between the **nvola-api** (invoice processor) and our new **receipt-api** (receipt processor).

---

## 🔄 Core Differences

### Purpose & Use Case

| Aspect | Invoice API (nvola-api) | Receipt API |
|--------|------------------------|-------------|
| **Primary Use** | B2B billing & accounting | B2C retail & expense tracking |
| **Document Type** | Formal invoices | Retail receipts |
| **Time Sensitivity** | Due dates, payment terms | Immediate payment |
| **Transaction Type** | Credit-based | Cash/immediate payment |
| **Volume** | Lower volume, higher value | High volume, lower value |

---

## 📋 Data Model Comparison

### Core Fields

| Invoice Field | Receipt Field | Why Different? |
|--------------|---------------|----------------|
| `vendor_name` | `merchant_name` | "Merchant" better suits retail context |
| `invoice_number` | `receipt_number` | Different numbering systems |
| `invoice_date` | `receipt_date` + `receipt_time` | Receipts track exact time |
| `due_date` | ❌ Removed | Receipts are paid immediately |
| `payment_terms` | ❌ Removed | Not applicable for receipts |
| `subtotal` | `subtotal` | ✅ Same |
| `tax_amount` | `tax_amount` | ✅ Same |
| `total_amount` | `total_amount` | ✅ Same |
| `currency` | `currency` | ✅ Same |
| ❌ Not present | `tip_amount` | NEW - Common in restaurants |
| ❌ Not present | `discount_amount` | NEW - Common in retail |

### Metadata Fields

| Invoice Metadata | Receipt Metadata | Notes |
|-----------------|------------------|-------|
| `category` | `category` | ✅ Same concept, different values |
| `country` | `store_location` | More specific address |
| `payment_terms` | `payment_method` | Immediate vs terms |
| ❌ | `store_phone` | NEW - Store contact |
| ❌ | `payment_last_four` | NEW - Card tracking |
| ❌ | `cashier` | NEW - Employee info |
| ❌ | `register_number` | NEW - POS system |
| ❌ | `transaction_id` | NEW - Transaction tracking |

### Line Items

| Invoice Line Item | Receipt Line Item | Difference |
|------------------|-------------------|------------|
| `description` | `description` | ✅ Same |
| `quantity` | `quantity` | ✅ Same |
| `unit_price` | `unit_price` | ✅ Same |
| ❌ | `total_price` | NEW - Line total |
| ❌ | `category` | NEW - Item categorization |

---

## 📝 Complete Schema Examples

### Invoice API Response
```json
{
  "status": "success",
  "data": {
    "vendor_name": "Acme Corp",
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-12-01",
    "due_date": "2024-12-31",
    "total_amount": 1500.00,
    "currency": "USD",
    "tax_amount": 150.00,
    "line_items": [
      {
        "description": "Web Development Services",
        "quantity": 40,
        "unit_price": 35.00
      }
    ],
    "metadata": {
      "category": "Professional Services",
      "country": "United States",
      "payment_terms": "Net 30"
    }
  }
}
```

### Receipt API Response
```json
{
  "status": "success",
  "data": {
    "merchant_name": "Target",
    "receipt_number": "0012-5678-9012",
    "receipt_date": "2024-12-05",
    "receipt_time": "14:32",
    "subtotal": 45.67,
    "tax_amount": 3.89,
    "tip_amount": null,
    "discount_amount": 5.00,
    "total_amount": 44.56,
    "currency": "USD",
    "line_items": [
      {
        "description": "Organic Apples",
        "quantity": 3,
        "unit_price": 2.99,
        "total_price": 8.97,
        "category": "Produce"
      },
      {
        "description": "Laundry Detergent",
        "quantity": 1,
        "unit_price": 12.99,
        "total_price": 12.99,
        "category": "Household"
      }
    ],
    "metadata": {
      "store_location": "123 Main St, NYC",
      "store_phone": "(212) 555-0100",
      "payment_method": "Credit Card",
      "payment_last_four": "4242",
      "cashier": "Sarah M.",
      "register_number": "5",
      "transaction_id": "TXN-20241205-143201",
      "category": "Retail"
    }
  }
}
```

---

## 🏗️ Architecture Comparison

Both APIs share the same architecture:

```
User Upload → OCR (Tesseract) → LLM (OpenAI) → Structured JSON
```

### Shared Components
- ✅ FastAPI framework
- ✅ Pydantic validation
- ✅ Tesseract OCR
- ✅ OpenAI GPT models
- ✅ Docker containerization
- ✅ pdf2image for PDFs

### Different Components
- ❌ None - same tech stack, different schemas

---

## 🎨 Category Differences

### Invoice Categories
- Professional Services
- Software/SaaS
- Consulting
- Marketing
- Legal Services
- Construction
- Manufacturing
- Wholesale

### Receipt Categories
- Groceries
- Dining/Restaurants
- Retail/Shopping
- Gas/Fuel
- Entertainment
- Pharmacy
- Hotels
- Transportation

---

## 💼 Use Case Scenarios

### When to Use Invoice API

#### 1. B2B Billing System
```python
# Process vendor invoice
invoice = process_invoice("vendor_invoice.pdf")
# Track payment due date
alert_if_due_soon(invoice['due_date'])
# Process payment terms
apply_payment_terms(invoice['payment_terms'])
```

#### 2. Accounts Payable
- Track vendor relationships
- Manage payment schedules
- Handle credit terms
- Process purchase orders

#### 3. Professional Services
- Law firms tracking billable hours
- Consulting firms
- B2B service providers

---

### When to Use Receipt API

#### 1. Expense Reimbursement
```python
# Employee submits receipt
receipt = process_receipt("lunch_receipt.jpg")
# Auto-categorize
if receipt['metadata']['category'] == 'Dining':
    create_expense_report(receipt)
```

#### 2. Personal Finance App
- Budget tracking
- Spending analysis
- Tax deduction tracking
- Warranty management

#### 3. Small Business Accounting
- Daily sales tracking
- Expense management
- Receipt archival
- Quick audits

---

## 🔍 LLM Prompt Differences

### Invoice Prompt Focus
```
Extract formal business invoice data:
- Vendor information and credentials
- Invoice numbering system
- Payment terms and due dates
- Detailed line items with descriptions
- Professional service categories
```

### Receipt Prompt Focus
```
Extract retail receipt data:
- Store/merchant name
- Exact date and time of purchase
- Individual product details
- Payment method used
- Store location and cashier info
- Discounts and promotions
```

---

## 📊 Performance Comparison

| Metric | Invoice API | Receipt API | Notes |
|--------|------------|-------------|-------|
| Avg Processing Time | 3-8 sec | 3-8 sec | Same |
| OCR Complexity | Medium | Medium-High | Receipts often smaller print |
| LLM Tokens | ~500-800 | ~400-700 | Receipts usually shorter |
| Cost per Document | $0.002-0.004 | $0.001-0.003 | Slightly cheaper |
| Accuracy Target | 95%+ | 90%+ | Receipts more variable |

---

## 🔄 Migration & Integration

### Can They Work Together?

**Yes!** Many businesses need both:

```python
def process_document(file_path):
    """Auto-detect document type and route to correct API"""
    
    # Quick heuristic check
    if is_formal_invoice(file_path):
        return invoice_api.process(file_path)
    else:
        return receipt_api.process(file_path)
```

### Unified Response Format

Create a wrapper that normalizes both:

```python
class UnifiedDocument:
    document_type: str  # 'invoice' or 'receipt'
    merchant_name: str
    document_number: str
    date: date
    total_amount: float
    items: List[Item]
    # ... other common fields
```

---

## 🎯 Accuracy Considerations

### Invoice API Challenges
- Complex line item descriptions
- Variable numbering formats
- International formats
- Multi-page invoices
- Special payment terms

### Receipt API Challenges
- Small, faded print
- Thermal paper degradation
- Variable layouts across stores
- Handwritten receipts
- Crumpled or damaged receipts
- Multiple similar items

---

## 🔐 Security & Compliance

### Invoice API Concerns
- Business financial data
- Vendor information
- Payment terms (sensitive)
- Often contains PII
- May require encryption at rest

### Receipt API Concerns
- Personal spending data
- Payment card information
- Location tracking (store address)
- Potentially tax-sensitive
- Privacy regulations (GDPR, etc.)

---

## 💰 Cost Analysis

### Per-Document Cost (OpenAI API)

| API | Model | Avg Tokens | Cost per Doc | Monthly (1000 docs) |
|-----|-------|------------|--------------|---------------------|
| Invoice | GPT-4o-mini | 700 | $0.003 | $3.00 |
| Receipt | GPT-4o-mini | 500 | $0.002 | $2.00 |
| Invoice | GPT-4o | 700 | $0.021 | $21.00 |
| Receipt | GPT-4o | 500 | $0.015 | $15.00 |

*Prices approximate as of Dec 2024*

---

## 🚀 Deployment Strategies

### Invoice API
- Often deployed internally (private network)
- Lower volume, can use smaller instances
- May need higher uptime SLAs
- Integration with accounting software

### Receipt API
- Can be public-facing (with auth)
- Higher volume, needs scaling
- Can tolerate brief downtime
- Mobile app integration common

---

## 📈 Scaling Recommendations

### Invoice API
```yaml
# Recommended deployment
instances: 2-3
memory: 2GB per instance
concurrent_requests: 10-20
database: Required for tracking
```

### Receipt API
```yaml
# Recommended deployment
instances: 3-5 (auto-scale)
memory: 1-2GB per instance
concurrent_requests: 50-100
database: Optional (store results elsewhere)
caching: Recommended
```

---

## 🔧 Customization Guide

### Adding Custom Fields

#### To Invoice API:
```python
# Add contract_number field
class InvoiceData(BaseModel):
    # ... existing fields
    contract_number: Optional[str] = None
```

#### To Receipt API:
```python
# Add loyalty_points field
class ReceiptMetadata(BaseModel):
    # ... existing fields
    loyalty_points: Optional[int] = None
```

---

## 📚 Summary

| Aspect | Invoice API | Receipt API | Best For |
|--------|-------------|-------------|----------|
| **Document Type** | Formal invoices | Retail receipts | Different contexts |
| **Payment Model** | Credit/terms | Immediate | B2B vs B2C |
| **Time Tracking** | Dates only | Date + time | Granularity needs |
| **Metadata** | Business-focused | Consumer-focused | Target audience |
| **Integration** | ERP/accounting | Mobile/expense apps | Platform type |
| **Volume** | Lower, larger $ | Higher, smaller $ | Transaction pattern |
| **Complexity** | More structured | More variable | Document format |

---

## 🎓 Recommendations

### Use Both When:
- You run a business that has both B2B and B2C transactions
- You need to track both vendor invoices AND employee expenses
- You're building a comprehensive financial management platform

### Choose Invoice API When:
- Primary focus is B2B transactions
- Payment terms and due dates are critical
- You need formal document tracking
- Integration with accounting systems is priority

### Choose Receipt API When:
- Primary focus is B2C/retail transactions
- Expense tracking and reimbursement is the goal
- Mobile-first approach is needed
- Volume is high, values are lower

---

## 🔗 Related Resources

- [Invoice API Documentation](https://github.com/RichardTrujilloTorres/nvola-api)
- [Receipt API Documentation](./README.md)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [OpenAI API Pricing](https://openai.com/pricing)

---

**Need help deciding? Consider your primary use case and document volume.**
