import requests

res = requests.post("http://127.0.0.1:8000/login", json={
    "email": "konstantin123@example.com",
    "password": "securepass12345"
})

print("📦 Ответ от сервера:", res.status_code)
print("🔍 JSON:", res.json())

token = res.json()["access_token"]

with open("token.txt", "w") as f:
    f.write(token)
