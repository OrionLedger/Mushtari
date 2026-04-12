import requests
import sys

URL = "http://localhost:8000"

def verify():
    print("🚀 Starting UAT Verification...")
    
    # 1. Health check
    try:
        r = requests.get(f"{URL}/health")
        r.raise_for_status()
        print("✅ Health Check Passed")
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False

    # 2. Metrics check
    try:
        r = requests.get(f"{URL}/metrics")
        r.raise_for_status()
        print("✅ Prometheus Metrics Available")
    except Exception as e:
        print(f"❌ Metrics Check Failed: {e}")
        return False

    # 3. API Docs check
    try:
        r = requests.get(f"{URL}/docs")
        r.raise_for_status()
        print("✅ Swagger Docs Available")
    except Exception as e:
        print(f"❌ Docs Check Failed: {e}")
        return False

    print("\n🎉 UAT Verification Successful!")
    return True

if __name__ == "__main__":
    if not verify():
        sys.exit(1)
