from twilio.rest import Client
import os


def make_outbound_call(to_number: str, message: str):
    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )

    call = client.calls.create(
        to=to_number,                       # Indian number
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        twiml=f"""
        <Response>
            <Say voice="alice">
                {message}
            </Say>
        </Response>
        """
    )

    return call.sid
