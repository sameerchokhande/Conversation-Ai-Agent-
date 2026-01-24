from dotenv import load_dotenv
import os

# ======================================
# LOAD ENVIRONMENT VARIABLES FIRST
# ======================================
load_dotenv()

print("GOOGLE_API_KEY loaded in main:", bool(os.getenv("GOOGLE_API_KEY")))

BASE_URL = os.getenv("PUBLIC_BASE_URL")  # e.g. https://xxxx.ngrok-free.app

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from app.agents.agent import agent_executor
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather


app = FastAPI()


# ======================================
# INBOUND VOICE WEBHOOK (USER → AI)
# ======================================
@app.post("/voice", response_class=PlainTextResponse)
async def voice_webhook(request: Request):
    form = await request.form()
    user_speech = form.get("SpeechResult")

    response = VoiceResponse()

    # ----------------------------------
    # FIRST CALL (NO SPEECH YET)
    # ----------------------------------
    if not user_speech:
        gather = Gather(
            input="speech",
            action=f"{BASE_URL}/voice",
            method="POST",
            timeout=5,
            speechTimeout="auto"
        )

        gather.say(
            "Welcome to Smile Care Dental Clinic. "
            "Please tell me how can I help you today."
        )

        response.append(gather)

        # Fallback if user says nothing
        response.say(
            "We did not receive your response. "
            "Please call again. Thank you."
        )

        return str(response)

    # ----------------------------------
    # USER SPOKE → AI PROCESSING
    # ----------------------------------
    try:
        result = agent_executor.invoke({"input": user_speech})
        agent_reply = result["output"]
    except Exception as e:
        print("Agent error:", e)
        response.say(
            "Sorry, I am having trouble understanding right now. "
            "Please try again later."
        )
        return str(response)

    # Say AI response
    response.say(agent_reply)

    # ----------------------------------
    # CONTINUE CONVERSATION
    # ----------------------------------
    gather = Gather(
        input="speech",
        action=f"{BASE_URL}/voice",
        method="POST",
        timeout=5,
        speechTimeout="auto"
    )

    gather.say(
        "Is there anything else I can help you with?"
    )

    response.append(gather)

    response.say(
        "Thank you for calling Smile Care Dental Clinic. Goodbye."
    )

    return str(response)


# ======================================
# MANUAL OUTBOUND DEMO CALL (AI → USER)
# ======================================
@app.get("/demo-outbound-call")
def demo_outbound_call():
    """
    Manual outbound call demo.
    Does NOT require ISD recharge on Indian number.
    """

    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )

    to_number = "+919766899198"  # 🔴 replace with your Indian number

    call = client.calls.create(
        to=to_number,
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        twiml="""
        <Response>
            <Say voice="alice">
                <prosody rate="85%">
                    Hello.
                    <break time="0.6s"/>
                    This is a reminder call from Smile Care Dental Clinic.
                    <break time="0.6s"/>
                    Your dental appointment is scheduled for tomorrow at ten a.m.
                    <break time="0.6s"/>
                    If you need to reschedule or cancel, please contact the clinic.
                    <break time="0.6s"/>
                    Thank you.
                </prosody>
            </Say>
        </Response>
        """
    )

    return {
        "status": "Outbound call triggered successfully",
        "call_sid": call.sid
    }


# ======================================
# OPTIONAL ROOT ENDPOINT (NO 404)
# ======================================
@app.get("/")
def home():
    return {"status": "Dental AI Agent is running"}
