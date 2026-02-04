import requests
import os
import json
from dotenv import load_dotenv

# ✅ Загружаем переменные из .env
load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

def get_token():
    if not EMAIL or not PASSWORD:
        print("❌ EMAIL or PASSWORD not found in .env")
        return None

    response = requests.post(f"{BASE_URL}/login", json={
        "email": EMAIL,
        "password": PASSWORD
    })

    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ ACCESS TOKEN:", token)
        with open(".token", "w") as f:
            f.write(token)
        return token
    else:
        print("❌ LOGIN FAILED:", response.status_code, response.text)
        return None

if __name__ == "__main__":
    get_token()

