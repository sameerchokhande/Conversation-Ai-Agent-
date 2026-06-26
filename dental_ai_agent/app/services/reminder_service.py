# app/services/reminder_service.py

import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)


def make_reminder_call(phone, appointment_id):

    call = client.calls.create(
        to=phone,
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        url=f"{os.getenv('BASE_URL')}/reminder/{appointment_id}"
    )

    print("📞 Reminder Call SID:", call.sid)