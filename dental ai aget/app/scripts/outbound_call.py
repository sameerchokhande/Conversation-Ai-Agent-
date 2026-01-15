from app.services.retell import outbound_call

outbound_call(
    phone="+91XXXXXXXXXX",
    message="Hello, this is a reminder for your dental appointment tomorrow at 10 AM."
)
