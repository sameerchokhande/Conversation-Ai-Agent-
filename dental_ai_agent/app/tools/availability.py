from langchain.tools import tool
from app.db.connection import get_db


@tool
def check_slot(doctor: str, date: str) -> str:
    """
    Check available slots for a doctor on a given date
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT time FROM appointments WHERE doctor=%s AND date=%s AND status='scheduled'",
        (doctor, date)
    )

    booked = [row[0] for row in cursor.fetchall()]

    if not booked:
        return f"Doctor {doctor} has all slots available on {date}."

    return f"Booked slots for Dr. {doctor} on {date}: {booked}"
