from app.db.connection import get_db
from langchain.tools import tool

# =========================
# PURE DB FUNCTION (FASTAPI)
# =========================
def book_slot_db(
    patient_name: str,
    address: str,
    reason: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    call_sid: str
) -> str:
    """
    Book a new appointment in DB
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO appointments
        (call_sid, patient_name, address, reason, doctor_name,
         appointment_date, appointment_time, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,'scheduled')
        """,
        (
            call_sid,
            patient_name,
            address,
            reason,
            doctor_name,
            appointment_date,
            appointment_time
        )
    )

    db.commit()
    return "Your appointment has been successfully booked."


# =========================
# LANGCHAIN TOOL (OPTIONAL)
# =========================
@tool
def book_slot(input: dict) -> str:
    """
    Book appointment using AI agent
    """
    return book_slot_db(**input)
