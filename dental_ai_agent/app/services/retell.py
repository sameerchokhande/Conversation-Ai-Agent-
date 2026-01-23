import requests
from app.config import settings

def outbound_call(phone: str, message: str):
    url = "https://api.retell.ai/call"
    headers = {
        "Authorization": f"Bearer {settings.RETELL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": phone,
        "agent_id": settings.RETELL_AGENT_ID,
        "message": message
    }
    requests.post(url, headers=headers, json=payload)
