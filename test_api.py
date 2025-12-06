"""
Simple test script for the Receipt Processing API
"""
import requests
import json
import sys
from pathlib import Path


def test_health():
    """Test the health endpoint"""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"✅ Status: {response.status_code}")
        print(f"📊 Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_process_receipt(file_path: str):
    """Test the receipt processing endpoint"""
    print(f"\n🧾 Testing receipt processing with: {file_path}")
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f)}
            response = requests.post(
                "http://localhost:8000/process-receipt",
                files=files
            )
        
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Receipt Data:")
            print(json.dumps(data, indent=2, default=str))
            return True
        else:
            print(f"❌ Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Receipt Processing API Test Suite\n")
    print("=" * 50)
    
    # Test health
    health_ok = test_health()
    
    if not health_ok:
        print("\n❌ Health check failed! Make sure the API is running.")
        print("   Run: uvicorn app.main:app --reload")
        sys.exit(1)
    
    # Test receipt processing if file provided
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        receipt_ok = test_process_receipt(file_path)
        
        if receipt_ok:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Receipt processing failed!")
            sys.exit(1)
    else:
        print("\n💡 To test receipt processing, run:")
        print("   python test_api.py path/to/receipt.jpg")
    
    print("=" * 50)


if __name__ == "__main__":
    main()
