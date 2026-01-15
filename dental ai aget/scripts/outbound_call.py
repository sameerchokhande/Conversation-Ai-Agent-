from twilio.rest import Client
from app.config import  (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER
)

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

client.calls.create(
    to="",          # Patient number
    from_=TWILIO_PHONE_NUMBER,   # Your Twilio number
    url="https://yourdomain.com/voice"
)
