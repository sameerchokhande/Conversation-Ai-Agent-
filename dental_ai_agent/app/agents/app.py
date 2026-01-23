from fastapi import FastAPI, Request
from twilio.twiml.voice_response import VoiceResponse
from agent import agent_executor

app = FastAPI()

@app.post("/voice")
async def voice_webhook(request: Request):
    form = await request.form()
    user_speech = form.get("SpeechResult")

    response = VoiceResponse()

    if not user_speech:
        gather = response.gather(
            input="speech",
            action="/voice",
            timeout=5
        )
        gather.say(
            "Welcome to Smile Care Dental. How can I help you today?"
        )
        return str(response)

    ai_reply = agent_executor.invoke({
        "input": user_speech
    })["output"]

    gather = response.gather(
        input="speech",
        action="/voice",
        timeout=5
    )
    gather.say(ai_reply)

    return str(response)
