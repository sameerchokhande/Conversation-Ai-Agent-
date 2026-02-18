from dotenv import load_dotenv
import os

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client

from app.db.connection import get_db
from app.tools.booking import book_slot_db
from app.services.nlp_processor import extract_appointment_data

app = FastAPI()
CALL_SESSIONS = {}

# =========================
# CLEAR VOICE FUNCTION (Fix Distorted Audio)
# =========================
def speak(response, text, lang="en-IN"):
    response.say(
        text,
        voice="Polly.Aditi",   # Clear Indian neural voice
        language=lang
    )

# =========================
# LANGUAGE CONFIG
# =========================
LANG_MAP = {
    "1": {"code": "en", "twilio": "en-IN"},
    "2": {"code": "hi", "twilio": "hi-IN"},
    "3": {"code": "mr", "twilio": "mr-IN"},
}

MESSAGES = {
    "select_lang": "Press 1 for English. Press 2 for Hindi. Press 3 for Marathi.",

    "welcome": {
        "en": "Welcome to Smile Care Dental Clinic.",
        "hi": "स्माइल केयर डेंटल क्लिनिक में आपका स्वागत है।",
        "mr": "स्माईल केअर डेंटल क्लिनिक मध्ये आपले स्वागत आहे."
    },

    "ask_name": {
        "en": "Please say your full name.",
        "hi": "कृपया अपना पूरा नाम बताएं।",
        "mr": "कृपया आपले पूर्ण नाव सांगा."
    },

    "ask_address": {
        "en": "Please say your address.",
        "hi": "कृपया अपना पता बताएं।",
        "mr": "कृपया आपला पत्ता सांगा."
    },

    "ask_reason": {
        "en": "Please tell the reason for your visit.",
        "hi": "कृपया अपनी समस्या बताएं।",
        "mr": "कृपया आपल्या भेटीचे कारण सांगा."
    },

    "ask_doctor": {
        "en": "Please say the doctor's name.",
        "hi": "कृपया डॉक्टर का नाम बताएं।",
        "mr": "कृपया डॉक्टरांचे नाव सांगा."
    },

    "ask_date": {
        "en": "Please say your preferred appointment date.",
        "hi": "कृपया अपॉइंटमेंट की तारीख बताएं।",
        "mr": "कृपया अपॉइंटमेंटची तारीख सांगा."
    },

    "ask_time": {
        "en": "Please say your preferred appointment time.",
        "hi": "कृपया अपॉइंटमेंट का समय बताएं।",
        "mr": "कृपया अपॉइंटमेंटची वेळ सांगा."
    },

    "confirm": {
        "en": "Press 1 to confirm. Press 2 to cancel.",
        "hi": "पुष्टि के लिए 1 दबाएं। रद्द करने के लिए 2 दबाएं।",
        "mr": "पुष्टीसाठी 1 दाबा. रद्द करण्यासाठी 2 दाबा."
    },

    "error": {
        "en": "Sorry, something went wrong.",
        "hi": "क्षमा करें, कुछ समस्या हुई।",
        "mr": "माफ करा, काही समस्या झाली."
    }
}

# =========================
# INBOUND VOICE WEBHOOK
# =========================
@app.post("/voice", response_class=PlainTextResponse)
async def voice_webhook(request: Request):

    form = await request.form()
    call_sid = form.get("CallSid")
    digits = form.get("Digits")
    speech = form.get("SpeechResult")

    print("\n📞 STEP:", CALL_SESSIONS.get(call_sid, {}).get("step"))
    print("🎤 RAW SPEECH:", speech)
    print("🔢 DIGITS:", digits)

    response = VoiceResponse()

    if call_sid not in CALL_SESSIONS:
        CALL_SESSIONS[call_sid] = {
            "step": "language",
            "lang": None,
            "twilio_lang": "en-IN",
            "data": {}
        }

    session = CALL_SESSIONS[call_sid]
    step = session["step"]

    # ================= LANGUAGE SELECTION =================
    if step == "language" and not digits:
        gather = Gather(input="dtmf", num_digits=1, action="/voice", method="POST")
        speak(gather, MESSAGES["select_lang"])
        response.append(gather)
        return str(response)

    if step == "language" and digits:
        if digits in LANG_MAP:
            session["lang"] = LANG_MAP[digits]["code"]
            session["twilio_lang"] = LANG_MAP[digits]["twilio"]
            session["step"] = "name"

            speak(response, MESSAGES["welcome"][session["lang"]], session["twilio_lang"])

            gather = Gather(
                input="speech",
                action="/voice",
                method="POST",
                speech_timeout="auto",
                language=session["twilio_lang"],
                speech_model="phone_call"
            )
            speak(gather, MESSAGES["ask_name"][session["lang"]], session["twilio_lang"])
            response.append(gather)
            return str(response)

        else:
            speak(response, "Invalid selection.")
            response.hangup()
            return str(response)

    lang = session["lang"]
    twilio_lang = session["twilio_lang"]

    # ================= BOOKING FLOW =================

    if step == "name" and speech:
        session["data"]["patient_name"] = speech
        print("🧾 SESSION DATA:", session["data"])
        session["step"] = "address"

        gather = Gather(input="speech", action="/voice", method="POST",
                        speech_timeout="auto", language=twilio_lang,
                        speech_model="phone_call")
        speak(gather, MESSAGES["ask_address"][lang], twilio_lang)
        response.append(gather)
        return str(response)

    if step == "address" and speech:
        session["data"]["address"] = speech
        print("🧾 SESSION DATA:", session["data"])
        session["step"] = "reason"

        gather = Gather(input="speech", action="/voice", method="POST",
                        speech_timeout="auto", language=twilio_lang,
                        speech_model="phone_call")
        speak(gather, MESSAGES["ask_reason"][lang], twilio_lang)
        response.append(gather)
        return str(response)

    if step == "reason" and speech:
        session["data"]["reason"] = speech
        print("🧾 SESSION DATA:", session["data"])
        session["step"] = "doctor"

        gather = Gather(input="speech", action="/voice", method="POST",
                        speech_timeout="auto", language=twilio_lang,
                        speech_model="phone_call")
        speak(gather, MESSAGES["ask_doctor"][lang], twilio_lang)
        response.append(gather)
        return str(response)

    if step == "doctor" and speech:
        session["data"]["doctor_name"] = speech
        print("🧾 SESSION DATA:", session["data"])
        session["step"] = "date"

        gather = Gather(input="speech", action="/voice", method="POST",
                        speech_timeout="auto", language=twilio_lang,
                        speech_model="phone_call")
        speak(gather, MESSAGES["ask_date"][lang], twilio_lang)
        response.append(gather)
        return str(response)

    if step == "date" and speech:
        session["data"]["appointment_date"] = speech
        print("🧾 SESSION DATA:", session["data"])
        session["step"] = "time"

        gather = Gather(input="speech", action="/voice", method="POST",
                        speech_timeout="auto", language=twilio_lang,
                        speech_model="phone_call")
        speak(gather, MESSAGES["ask_time"][lang], twilio_lang)
        response.append(gather)
        return str(response)

    if step == "time" and speech:
        session["data"]["appointment_time"] = speech
        print("🧾 SESSION DATA:", session["data"])
        session["step"] = "confirm"

        gather = Gather(input="dtmf", num_digits=1, action="/voice", method="POST")
        speak(gather, MESSAGES["confirm"][lang], twilio_lang)
        response.append(gather)
        return str(response)

    # ================= CONFIRM =================
    if step == "confirm" and digits:
        if digits == "1":

            structured = extract_appointment_data(
                f"""
                Name: {session['data'].get('patient_name','')}
                Address: {session['data'].get('address','')}
                Reason: {session['data'].get('reason','')}
                Doctor: {session['data'].get('doctor_name','')}
                Date: {session['data'].get('appointment_date','')}
                Time: {session['data'].get('appointment_time','')}
                """
            )

            print("\n📦 STRUCTURED DATA BEFORE DB SAVE:")
            print(structured)

            if not structured:
                speak(response, MESSAGES["error"][lang], twilio_lang)
            else:
                msg = book_slot_db(
                    patient_name=structured["patient_name"],
                    address=structured["address"],
                    reason=structured["reason"],
                    doctor_name=structured["doctor_name"],
                    appointment_date=structured["appointment_date"],
                    appointment_time=structured["appointment_time"],
                    call_sid=call_sid,
                )
                speak(response, msg, twilio_lang)

        else:
            speak(response, "Cancelled.", twilio_lang)

        CALL_SESSIONS.pop(call_sid, None)
        response.hangup()
        return str(response)

    speak(response, MESSAGES["error"][lang], twilio_lang)
    response.hangup()
    return str(response)
