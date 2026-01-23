from dotenv import load_dotenv
import os

# 🔴 VERY IMPORTANT: load env FIRST
load_dotenv()

print("GOOGLE_API_KEY loaded in main:", bool(os.getenv("GOOGLE_API_KEY")))

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

# 🔴 Import agent AFTER env is loaded
from app.agents.agent import agent_executor


app = FastAPI()


@app.post("/voice", response_class=PlainTextResponse)
async def voice_webhook(request: Request):
    form = await request.form()
    user_speech = form.get("SpeechResult")

    try:
        from twilio.twiml.voice_response import VoiceResponse
    except ImportError:
        return PlainTextResponse("Twilio dependency not installed", status_code=501)

    response = VoiceResponse()

    # 1️⃣ First call (no speech yet)
    if not user_speech:
        gather = response.gather(
            input="speech",
            action="/voice",
            method="POST",
            timeout=5,
            speechTimeout="auto"
        )
        gather.say(
            "Welcome to Smile Care Dental Clinic. How can I help you today?"
        )
        return str(response)

    # 2️⃣ User spoke → send to agent
    try:
        result = agent_executor.invoke({"input": user_speech})
        agent_reply = result["output"]
    except Exception as e:
        print("Agent error:", e)
        response.say(
            "Sorry, I am having trouble right now. Please try again."
        )
        return str(response)

    # 3️⃣ Say agent response
    response.say(agent_reply)

    # 4️⃣ Continue the conversation (LOOP)
    gather = response.gather(
        input="speech",
        action="/voice",
        method="POST",
        timeout=5,
        speechTimeout="auto"
    )
    gather.say("Is there anything else I can help you with?")

    return str(response)
