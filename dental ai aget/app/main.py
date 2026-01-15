from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
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

    # First call (no speech yet)
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

    # User spoke → send to agent
    try:
        agent_reply = agent_executor.invoke(
            {"input": user_speech}
        )["output"]
    except Exception as e:
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
