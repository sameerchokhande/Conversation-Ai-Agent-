from langchain.tools import tool
from app.db.connection import get_db


# ✅ Plain DB function (for IVR / FastAPI)
def check_slot_db(doctor_name: str, appointment_date: str) -> str:
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT appointment_time
        FROM appointments
        WHERE doctor_name=%s
          AND appointment_date=%s
          AND status='scheduled'
        """,
        (doctor_name, appointment_date)
    )

    booked = [row[0] for row in cursor.fetchall()]

    if not booked:
        return f"Doctor {doctor_name} has all slots available on {appointment_date}."

    return (
        f"Booked slots for Doctor {doctor_name} on {appointment_date} are "
        + ", ".join(booked)
    )


# ✅ LangChain tool (ONLY for agent usage)
@tool
def check_slot(doctor_name: str, appointment_date: str) -> str:
    """
    Check available appointment slots for a given doctor on a specific date.
    """
    return check_slot_db(doctor_name, appointment_date)
