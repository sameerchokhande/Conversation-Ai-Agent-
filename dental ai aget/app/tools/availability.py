from langchain.tools import tool
from app.db.connection import get_db

@tool
def check_availability(doctor: str, date: str):
    """Check available slots for a doctor"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT time FROM appointments WHERE doctor=%s AND date=%s AND status='scheduled'",
        (doctor, date)
    )
    booked = [row[0] for row in cursor.fetchall()]
    return f"Booked slots: {booked}"

