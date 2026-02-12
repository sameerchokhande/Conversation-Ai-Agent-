from dotenv import load_dotenv
import os

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client

from app.db.connection import get_db
from app.tools.booking import book_slot_db
from app.tools.availability import check_slot_db
from app.tools.cancel import cancel_slot_db
from app.tools.reschedule import reschedule_slot_db


app = FastAPI()

# =========================
# IN-MEMORY SESSION STORE
# =========================
CALL_SESSIONS = {}


# =========================
# DB HELPER
# =========================
def get_latest_appointment_by_call_sid(call_sid):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id, doctor_name, appointment_date, appointment_time
        FROM appointments
        WHERE call_sid=%s AND status='scheduled'
        ORDER BY id DESC
        LIMIT 1
        """,
        (call_sid,)
    )
    return cursor.fetchone()


# =========================
# INBOUND VOICE WEBHOOK
# =========================
@app.post("/voice", response_class=PlainTextResponse)
async def voice_webhook(request: Request):
    form = await request.form()

    call_sid = form.get("CallSid")
    digits = form.get("Digits")
    speech = form.get("SpeechResult")

    response = VoiceResponse()

    if call_sid not in CALL_SESSIONS:
        CALL_SESSIONS[call_sid] = {"step": "menu", "data": {}}

    session = CALL_SESSIONS[call_sid]
    step = session["step"]

    # ================= MENU =================
    if step == "menu" and not digits:
        gather = Gather(input="dtmf", num_digits=1, action="/voice", method="POST")
        gather.say(
            "Welcome to Smile Care Dental Clinic. "
            "Press 1 to book an appointment. "
            "Press 2 to reschedule an appointment. "
            "Press 3 to cancel an appointment."
        )
        response.append(gather)
        return str(response)

    if step == "menu" and digits:
        if digits == "1":
            session["step"] = "name"
            gather = Gather(input="speech", action="/voice", method="POST")
            gather.say("Please say your full name.")
            response.append(gather)
            return str(response)

        if digits == "2":
            session["step"] = "reschedule_date"
            gather = Gather(input="speech", action="/voice", method="POST")
            gather.say("Please say the new appointment date.")
            response.append(gather)
            return str(response)

        if digits == "3":
            session["step"] = "cancel_confirm"

    # ================= BOOKING FLOW =================
    if step == "name" and speech:
        session["data"]["patient_name"] = speech
        session["step"] = "address"
        gather = Gather(input="speech", action="/voice", method="POST")
        gather.say("Please say your address.")
        response.append(gather)
        return str(response)

    if step == "address" and speech:
        session["data"]["address"] = speech
        session["step"] = "reason"
        gather = Gather(input="speech", action="/voice", method="POST")
        gather.say("Please tell the reason for your visit.")
        response.append(gather)
        return str(response)

    if step == "reason" and speech:
        session["data"]["reason"] = speech
        session["step"] = "doctor"
        gather = Gather(input="speech", action="/voice", method="POST")
        gather.say("Please say the doctor's name.")
        response.append(gather)
        return str(response)

    if step == "doctor" and speech:
        session["data"]["doctor_name"] = speech
        session["step"] = "date"
        gather = Gather(input="speech", action="/voice", method="POST")
        gather.say("Please say your preferred appointment date.")
        response.append(gather)
        return str(response)

    if step == "date" and speech:
        session["data"]["appointment_date"] = speech
        availability = check_slot_db(
            session["data"]["doctor_name"],
            session["data"]["appointment_date"]
        )
        session["step"] = "time"
        gather = Gather(input="speech", action="/voice", method="POST")
        gather.say(f"{availability}. Please say your preferred appointment time.")
        response.append(gather)
        return str(response)

    if step == "time" and speech:
        session["data"]["appointment_time"] = speech
        session["step"] = "confirm"

        d = session["data"]
        gather = Gather(input="dtmf", num_digits=1, action="/voice", method="POST")
        gather.say(
            f"You want an appointment with Doctor {d['doctor_name']} "
            f"on {d['appointment_date']} at {d['appointment_time']}. "
            "Press 1 to confirm. Press 2 to cancel."
        )
        response.append(gather)
        return str(response)

    if step == "confirm" and digits:
        if digits == "1":
            msg = book_slot_db(
                patient_name=session["data"]["patient_name"],
                address=session["data"]["address"],
                reason=session["data"]["reason"],
                doctor_name=session["data"]["doctor_name"],
                appointment_date=session["data"]["appointment_date"],
                appointment_time=session["data"]["appointment_time"],
                call_sid=call_sid
            )
            response.say(msg)
        else:
            response.say("Your appointment was cancelled.")

        CALL_SESSIONS.pop(call_sid, None)
        response.hangup()
        return str(response)

    # ================= CANCEL FLOW =================
    if step == "cancel_confirm":
        appt = get_latest_appointment_by_call_sid(call_sid)
        if not appt:
            response.say("No active appointment found.")
            response.hangup()
            return str(response)

        session["data"]["appointment_id"] = appt["id"]
        gather = Gather(input="dtmf", num_digits=1, action="/voice", method="POST")
        gather.say(
            f"You have an appointment on {appt['appointment_date']} "
            f"at {appt['appointment_time']}. "
            "Press 1 to cancel. Press 2 to keep it."
        )
        session["step"] = "cancel_final"
        response.append(gather)
        return str(response)

    if step == "cancel_final" and digits:
        if digits == "1":
            response.say(cancel_slot_db(session["data"]["appointment_id"]))
        else:
            response.say("Your appointment was not cancelled.")

        CALL_SESSIONS.pop(call_sid, None)
        response.hangup()
        return str(response)

    # ================= RESCHEDULE FLOW =================
    if step == "reschedule_date" and speech:
        session["data"]["new_date"] = speech
        session["step"] = "reschedule_time"
        gather = Gather(input="speech", action="/voice", method="POST")
        gather.say("Please say the new appointment time.")
        response.append(gather)
        return str(response)

    if step == "reschedule_time" and speech:
        appt = get_latest_appointment_by_call_sid(call_sid)
        if not appt:
            response.say("No appointment found.")
            response.hangup()
            return str(response)

        response.say(
            reschedule_slot_db(
                appt["id"],
                session["data"]["new_date"],
                speech
            )
        )

        CALL_SESSIONS.pop(call_sid, None)
        response.hangup()
        return str(response)

    response.say("Sorry, something went wrong. Please call again.")
    response.hangup()
    return str(response)


# =========================
# OUTBOUND DEMO CALL
# =========================
@app.get("/demo-outbound-call")
def demo_outbound_call():
    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )

    call = client.calls.create(
        to="+919766899198",
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        twiml="<Response><Say>This is a demo appointment reminder.</Say></Response>"
    )

    return {"status": "Call triggered", "call_sid": call.sid}
