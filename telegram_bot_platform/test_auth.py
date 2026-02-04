import requests
from app.config import settings

def get_tokens():
    res = requests.post(f"{settings.BASE_URL}/login", json={
        "email": settings.EMAIL,
        "password": settings.PASSWORD
    })
    assert res.status_code == 200, f"Login failed: {res.text}"
    data = res.json()
    return data["access_token"], data["refresh_token"]

def test_me():
    access_token, _ = get_tokens()
    print("🧪 TOKEN USED IN TEST:", access_token)
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get(f"{settings.BASE_URL}/me", headers=headers)
    assert res.status_code == 200, f"/me failed: {res.text}"

def test_refresh():
    _, refresh_token = get_tokens()
    res = requests.post(f"{settings.BASE_URL}/refresh", json={
        "email": settings.EMAIL,
        "password": settings.PASSWORD
    })
    assert res.status_code == 200, f"/refresh failed: {res.text}"



