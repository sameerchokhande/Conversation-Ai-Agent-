from urllib import response

from requests import session
from twilio.rest import Client

from app.services.scheduler_service import start_scheduler
from dotenv import load_dotenv
import os
from datetime import datetime, time
import re

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from twilio.twiml.voice_response import VoiceResponse, Gather
from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.db.connection import get_db
from app.tools.booking import book_slot_db
from app.services.nlp_processor import extract_appointment_data
from routers.frontend import router as frontend_router

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(frontend_router)
CALL_SESSIONS = {}

from routers.reminder_router import (
    router as reminder_router
)

app.include_router(
    reminder_router
)



@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )



TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = "+19843711470"   # Twilio Number
MY_NUMBER = "+919766899198"      # Your Number

client = Client(TWILIO_SID, TWILIO_TOKEN)


# =========================
# CLINIC WORKING HOURS
# =========================
CLINIC_OPEN = time(9, 0)
CLINIC_CLOSE = time(19, 0)

# =========================
# VOICE FUNCTION
# =========================
def speak(response, text, lang="en-IN"):
    response.say(text, voice="Polly.Aditi", language=lang)

# =========================
# CLEAN DOCTOR NAME
# =========================
def clean_doctor_input(text):
    text = text.lower()
    text = re.sub(r"\bdoctor\b|\bdr\b|डॉक्टर|डॉक्टरांचे|डॉक्टरांचा|डॉक्टर", "", text)
    return text.strip()

# =========================
# ✅ NEW: NORMALIZE MULTILINGUAL TEXT
# =========================
def normalize_text(text):
    text = text.lower()

    mapping = {
        "पाटील": "patil",
        "शर्मा": "sharma",
        "मेहता": "mehta",
        "डॉक्टर": "",
    }

    for k, v in mapping.items():
        text = text.replace(k, v)

    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()


# =========================
# FETCH DOCTORS
# =========================
def get_doctors():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT name, available_from, available_to FROM doctors")
    return cursor.fetchall()

# =========================
# ✅ FINAL FIXED TIME PARSER
# =========================
def parse_time_input(text):
    if not text:
        return None

    text = text.lower().strip()

    # 🔥 Fix Twilio format
    text = text.replace("p.m.", "pm").replace("a.m.", "am")

    # Hindi/Marathi number mapping
    number_map = {
        "ek": "1", "do": "2", "teen": "3", "char": "4", "paanch": "5",
        "chhe": "6", "saat": "7", "aath": "8", "nau": "9", "das": "10",
        "gyarah": "11", "barah": "12",
        "don": "2", "paach": "5", "saha": "6", "daha": "10", "akra": "11", "bara": "12",
        "एक": "1", "दो": "2", "तीन": "3", "चार": "4", "पांच": "5",
        "छह": "6", "सात": "7", "आठ": "8", "नौ": "9", "दस": "10",
        "ग्यारह": "11", "बारह": "12",
        "दोन": "2", "तीन": "3", "चार": "4", "पाच": "5",
        "सहा": "6", "सात": "7", "आठ": "8", "नऊ": "9", "दहा": "10",
        "अकरा": "11", "बारा": "12"
    }

    for word, num in number_map.items():
        if word in text:
            text = text.replace(word, num)

    # Remove extra words
    text = text.replace("baje", "").replace("वाजता", "").replace("बजे", "")
    text = text.strip()

    # Default PM
    if "am" not in text and "pm" not in text:
        text += " pm"

    text = text.upper()

    formats = ["%I %p", "%I:%M %p"]

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).time()
        except:
            continue

    return None

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
        "en": "Hi this is yaleena. Welcome to Smile Care Dental Clinic.keep smiling keep shining",
        "hi": "स्माइल केयर डेंटल क्लिनिक में आपका स्वागत है।",
        "mr": "स्माईल केअर डेंटल क्लिनिक मध्ये आपले स्वागत आहे."
    },
    "ask_name": {
        "en": "Please say your full name.",
        "hi": "कृपया अपना पूरा नाम बताएं।",
        "mr": "कृपया आपले पूर्ण नाव सांगा."
    },
    "ask_address": {
        "en": "where do you come from.",
        "hi": "कृपया अपना पता बताएं।",
        "mr": "कृपया आपला पत्ता सांगा."
    },
    "ask_reason": {
        "en": "why do you feel like visiting doctor.",
        "hi": "कृपया अपनी समस्या बताएं।",
        "mr": "कृपया आपल्या भेटीचे कारण सांगा."
    },
    "ask_date": {
        "en": "Please say appointment date.",
        "hi": "कृपया अपॉइंटमेंट की तारीख बताएं।",
        "mr": "कृपया अपॉइंटमेंटची तारीख सांगा."
    },
    "ask_time": {
        "en": "At what time would you like to book an appointment.",
        "hi": "कृपया समय बताएं जैसे 2 PM.",
        "mr": "कृपया वेळ सांगा जसे 2 PM."
    },
    "doctor_not_found": {
        "en": "Doctor not found. Please say again.",
        "hi": "डॉक्टर नहीं मिले। कृपया फिर से बताएं।",
        "mr": "डॉक्टर सापडले नाहीत. कृपया पुन्हा सांगा."
    },
    "invalid_time": {
        "en": "Invalid time format. Please say again.",
        "hi": "गलत समय प्रारूप। कृपया फिर से बताएं।",
        "mr": "वेळ चुकीच्या स्वरूपात आहे. कृपया पुन्हा सांगा."
    },
    "clinic_time": {
        "en": "Clinic is open from 9 AM to 7 PM.",
        "hi": "क्लिनिक सुबह 9 से शाम 7 बजे तक खुला है।",
        "mr": "क्लिनिक सकाळी 9 ते संध्याकाळी 7 पर्यंत खुले आहे."
    },
    "confirm": {
        "en": "Press 1 to confirm. Press 2 to reschedule. Press 3 to cancel.",
        "hi": "पुष्टि के लिए 1 दबाएं। बदलने के लिए 2 दबाएं। रद्द करने के लिए 3 दबाएं।",
        "mr": "पुष्टीसाठी 1 दाबा. बदलासाठी 2 दाबा. रद्द करण्यासाठी 3 दाबा."
    },
    "error": {
        "en": "Sorry, something went wrong.",
        "hi": "क्षमा करें, कुछ समस्या हुई।",
        "mr": "माफ करा, काही समस्या झाली."
    }
}

def build_summary_text(data, lang):
    name = data.get("patient_name", "")
    doctor = data.get("doctor_name", "")
    date = data.get("appointment_date", "")
    appointment_time = data.get("appointment_time", "")

    if lang == "hi":
        return (
            f"आपका नाम {name} है। "
            f"डॉक्टर {doctor} हैं। "
            f"अपॉइंटमेंट की तारीख {date} है। "
            f"समय {appointment_time} है। "
            f"आपको स्माइल केयर डेंटल क्लिनिक, डेक्कन कॉर्नर, पुणे आना है।"
        )

    elif lang == "mr":
        return (
            f"आपले नाव {name} आहे. "
            f"डॉक्टर {doctor} आहेत. "
            f"अपॉइंटमेंटची तारीख {date} आहे. "
            f"वेळ {appointment_time} आहे. "
            f"आपल्याला स्माईल केअर डेंटल क्लिनिक, डेक्कन कॉर्नर, पुणे येथे यायचे आहे."
        )

    else:
        return (
            f"Your name is {name}. "
            f"Doctor is {doctor}. "
            f"Appointment date is {date}. "
            f"Appointment time is {appointment_time}. "
            f"You have to visit Smile Care Dental Clinic, Deccan Corner, Pune."
        )

# =========================
# WEBHOOK
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

    # ================= LANGUAGE =================
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

            gather = Gather(input="speech", action="/voice", method="POST",
                            speech_timeout="auto", language=session["twilio_lang"])
            speak(gather, MESSAGES["ask_name"][session["lang"]], session["twilio_lang"])
            response.append(gather)
            return str(response)

    lang = session["lang"]
    twilio_lang = session["twilio_lang"]

    # ================= NAME =================
    if step == "name" and speech:
        session["data"]["patient_name"] = speech
        print("🧾 SESSION:", session["data"])
        session["step"] = "address"

        gather = Gather(input="speech", action="/voice", method="POST",
                        speech_timeout="auto", language=twilio_lang)
        speak(gather, MESSAGES["ask_address"][lang], twilio_lang)
        response.append(gather)
        return str(response)

    # ================= ADDRESS =================
    if step == "address" and speech:
        session["data"]["address"] = speech
        print("🧾 SESSION:", session["data"])
        session["step"] = "reason"

        gather = Gather(input="speech", action="/voice", method="POST",
                        speech_timeout="auto", language=twilio_lang)
        speak(gather, MESSAGES["ask_reason"][lang], twilio_lang)
        response.append(gather)
        return str(response)

    # ================= REASON =================
    if step == "reason" and speech:
        session["data"]["reason"] = speech
        print("🧾 SESSION:", session["data"])

        doctors = get_doctors()
        session["available_doctors"] = doctors
        session["step"] = "doctor"

        doctor_names = ", ".join([d["name"] for d in doctors])

        if lang == "mr":
            msg = f"उपलब्ध डॉक्टर आहेत {doctor_names}. तुम्हाला कोणत्या डॉक्टरांकडे जायचे आहे?"
        elif lang == "hi":
            msg = f"उपलब्ध डॉक्टर हैं {doctor_names}. आप किस डॉक्टर से मिलना चाहते हैं?"
        else:
            msg = f"Available doctors are {doctor_names}. Which doctor would you like?"

        gather = Gather(input="speech", action="/voice", method="POST",
                        speech_timeout="auto", language=twilio_lang)
        speak(gather, msg, twilio_lang)
        response.append(gather)
        return str(response)

    # ================= DOCTOR =================
    if step == "doctor" and speech:

        cleaned_input = clean_doctor_input(speech)
        print("🧠 CLEANED INPUT:", cleaned_input)

        doctors = session.get("available_doctors", [])
        matched = None

        for d in doctors:
            db_name = d["name"].lower()
            db_clean = re.sub(r"\bdoctor\b|\bdr\b", "", db_name).strip()

            print("🔍 CHECK:", db_clean)

            if cleaned_input in db_clean or db_clean in cleaned_input:
                matched = d
                break

        if not matched:
            gather = Gather(input="speech", action="/voice", method="POST",
                            speech_timeout="auto", language=twilio_lang)
            speak(gather, MESSAGES["doctor_not_found"][lang], twilio_lang)
            response.append(gather)
            return str(response)

        session["data"]["doctor_name"] = matched["name"]
        print("🧾 SESSION:", session["data"])

        session["step"] = "date"

        gather = Gather(input="speech", action="/voice", method="POST",
                        speech_timeout="auto", language=twilio_lang)
        speak(gather, MESSAGES["ask_date"][lang], twilio_lang)
        response.append(gather)
        return str(response)

    # ================= DATE =================
    if step == "date" and speech:
        session["data"]["appointment_date"] = speech
        print("🧾 SESSION:", session["data"])
        session["step"] = "time"

        gather = Gather(input="speech", action="/voice", method="POST",
                        speech_timeout="auto", language=twilio_lang)
        speak(gather, MESSAGES["ask_time"][lang], twilio_lang)
        response.append(gather)
        return str(response)

    # ================= TIME =================
    if step == "time" and speech:

        parsed_time = parse_time_input(speech)

        if not parsed_time:
            speak(response, MESSAGES["invalid_time"][lang], twilio_lang)
            return str(response)

        if parsed_time < CLINIC_OPEN or parsed_time > CLINIC_CLOSE:
            speak(response, MESSAGES["clinic_time"][lang], twilio_lang)
            return str(response)

        # ✅ FIXED TO 12-HOUR FORMAT
        session["data"]["appointment_time"] = parsed_time.strftime("%I:%M %p")
        print("🧾 SESSION:", session["data"])

        session["step"] = "confirm"

        # Build appointment summary
        summary = build_summary_text(session["data"], lang)
        print("📢 SUMMARY:", summary)

        # Speak summary first
        speak(response, summary, twilio_lang)
        response.pause(length=1)

        # Then ask for confirmation
        gather = Gather(
        input="dtmf",
        num_digits=1,
        action="/voice",
        method="POST"
        )

        speak(
           gather,
            MESSAGES["confirm"][lang],
            twilio_lang
        )

        response.append(gather)
        return str(response)
        

 # ================= CONFIRM =================
    if step == "confirm" and digits:

        # ---------- BOOK APPOINTMENT ----------
        if digits == "1":

            try:
                structured = extract_appointment_data(
                    str(session["data"])
                )

                print("📦 STRUCTURED:", structured)

                if structured:

                    msg = book_slot_db(
                        patient_name=structured.get("patient_name", ""),
                        address=structured.get("address", ""),
                        reason=structured.get("reason", ""),
                        doctor_name=structured.get("doctor_name", ""),
                        appointment_date=structured.get("appointment_date", ""),
                        appointment_time=structured.get("appointment_time", ""),
                        call_sid=call_sid,
                    )

                    speak(response, msg, twilio_lang)
                    response.pause(length=2)

                else:
                    speak(
                        response,
                        MESSAGES["error"][lang],
                        twilio_lang
                    )

            except Exception as e:
                print("❌ BOOKING ERROR:", e)
                speak(
                    response,
                    MESSAGES["error"][lang],
                    twilio_lang
                )

            CALL_SESSIONS.pop(call_sid, None)
            response.hangup()
            return str(response)

        # ---------- RESCHEDULE ----------
        elif digits == "2":

            print("🔄 RESCHEDULE SELECTED")

            session["step"] = "date"

            gather = Gather(
                input="speech",
                action="/voice",
                method="POST",
                speech_timeout="auto",
                language=twilio_lang
            )

            if lang == "mr":
                msg = "कृपया नवीन अपॉइंटमेंटची तारीख सांगा."
            elif lang == "hi":
                msg = "कृपया नई अपॉइंटमेंट की तारीख बताएं।"
            else:
                msg = "Please say your new appointment date."

            speak(gather, msg, twilio_lang)
            response.append(gather)

            return str(response)

        # ---------- CANCEL ----------
        elif digits == "3":

            if lang == "mr":
                msg = "आपली अपॉइंटमेंट रद्द करण्यात आली आहे."
            elif lang == "hi":
                msg = "आपकी अपॉइंटमेंट रद्द कर दी गई है।"
            else:
                msg = "Your appointment has been cancelled."

            speak(response, msg, twilio_lang)
            response.pause(length=1)

            CALL_SESSIONS.pop(call_sid, None)
            response.hangup()
            return str(response)
        









def get_latest_appointment():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM appointments
        WHERE status='scheduled'
        ORDER BY id DESC
        LIMIT 1
    """)

    appointment = cursor.fetchone()

    cursor.close()
    db.close()

    return appointment
    
def make_reminder_call():

    appointment = get_latest_appointment()

    if not appointment:
        print("No scheduled appointments found.")
        return

    call = client.calls.create(
        to=MY_NUMBER,
        from_=TWILIO_NUMBER,
        url="https://4683-2409-40c2-841d-a746-e90b-7320-9ab-ce91.ngrok-free.app/reminder-voice"
    )

    print("Reminder call started:", call.sid)  

@app.post("/reminder-voice")
async def reminder_voice():

    appointment = get_latest_appointment()

    response = VoiceResponse()

    if not appointment:
        response.say(
            "No scheduled appointment found.",
            voice="Google.en-IN-Wavenet-A",
            language="en-IN"
        )
        return PlainTextResponse(
            str(response),
            media_type="application/xml"
        )

    name = appointment["patient_name"]
    doctor = appointment["doctor_name"]
    date = appointment["appointment_date"]
    appointment_time = appointment["appointment_time"]

    gather = Gather(
        input="dtmf",
        num_digits=1,
        action="/reminder-action",
        method="POST"
    )

    message = (
        f"Hello {name}. "
        f"This is a reminder from Smile Care Dental Clinic. "
        f"Your appointment with Doctor {doctor} "
        f"is scheduled on {date} at {appointment_time}. "
        f"Press 1 to confirm your appointment. "
        f"Press 2 to reschedule your appointment. "
        f"Press 3 to cancel your appointment."
    )

    gather.say(
        message,
        voice="Google.en-IN-Wavenet-A",
        language="en-IN"
    )

    response.append(gather)

    return PlainTextResponse(
        str(response),
        media_type="application/xml"
    )

@app.post("/reminder-action")
async def reminder_action(request: Request):

    form = await request.form()
    digits = form.get("Digits")

    response = VoiceResponse()

    if digits == "1":

        response.say(
            "Thank you. Your appointment has been confirmed.",
            voice="Google.en-IN-Wavenet-A",
            language="en-IN"
        )

    elif digits == "2":

        gather = Gather(
            input="speech",
            action="/reschedule-date",
            method="POST",
            speech_timeout="auto",
            language="en-IN"
        )

        gather.say(
            "Please say your new appointment date.",
            voice="Google.en-IN-Wavenet-A",
            language="en-IN"
        )

        response.append(gather)

        return PlainTextResponse(
            str(response),
            media_type="application/xml"
        )

    elif digits == "3":

        response.say(
            "Your appointment has been cancelled.",
            voice="Google.en-IN-Wavenet-A",
            language="en-IN"
        )

    else:

        response.say(
            "Invalid selection.",
            voice="Google.en-IN-Wavenet-A",
            language="en-IN"
        )

    response.hangup()

    return PlainTextResponse(
        str(response),
        media_type="application/xml"
    )



@app.post("/reschedule-date")
async def reschedule_date(request: Request):

    form = await request.form()
    new_date = form.get("SpeechResult")

    response = VoiceResponse()

    appointment = get_latest_appointment()

    if not appointment:
        response.say(
            "No appointment found.",
            voice="Google.en-IN-Wavenet-A",
            language="en-IN"
        )
        response.hangup()

        return PlainTextResponse(
            str(response),
            media_type="application/xml"
        )

    # Store temporarily
    CALL_SESSIONS["reminder"] = {
        "id": appointment["id"],
        "new_date": new_date
    }

    gather = Gather(
        input="speech",
        action="/reschedule-time",
        method="POST",
        speech_timeout="auto",
        language="en-IN"
    )

    gather.say(
        "Please say your new appointment time.",
        voice="Google.en-IN-Wavenet-A",
        language="en-IN"
    )

    response.append(gather)

    return PlainTextResponse(
        str(response),
        media_type="application/xml"
    )

@app.post("/reschedule-time")
async def reschedule_time(request: Request):

    form = await request.form()
    new_time = form.get("SpeechResult")

    response = VoiceResponse()

    reminder_data = CALL_SESSIONS.get("reminder")

    if not reminder_data:

        response.say(
            "Session expired. Please try again.",
            voice="Google.en-IN-Wavenet-A",
            language="en-IN"
        )

        response.hangup()

        return PlainTextResponse(
            str(response),
            media_type="application/xml"
        )

    appointment_id = reminder_data["id"]
    new_date = reminder_data["new_date"]

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE appointments
        SET appointment_date=%s,
            appointment_time=%s
        WHERE id=%s
        """,
        (
            new_date,
            new_time,
            appointment_id
        )
    )

    db.commit()
    cursor.close()
    db.close()

    CALL_SESSIONS.pop("reminder", None)

    response.say(
        f"Thank you. Your appointment has been rescheduled to "
        f"{new_date} at {new_time}.",
        voice="Google.en-IN-Wavenet-A",
        language="en-IN"
    )

    response.hangup()

    return PlainTextResponse(
        str(response),
        media_type="application/xml"
    )



@app.get("/test-reminder")
async def test_reminder():
    try:
        make_reminder_call()
        return {
            "status": "success",
            "message": "Reminder call initiated."
        }

    except Exception as e:
        print("❌ REMINDER ERROR:", e)

        return {
            "status": "failed",
            "error": str(e)
        }





from app.services.scheduler_service import (
    start_scheduler
    )

start_scheduler()