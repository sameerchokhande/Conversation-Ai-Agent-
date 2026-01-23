from langchain.tools import tool
from app.db.connection import get_db


@tool
def book_slot(name: str, phone: str, doctor: str, date: str, time: str) -> str:
    """
    Book a new appointment
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO appointments (name, phone, doctor, date, time, status)
        VALUES (%s, %s, %s, %s, %s, 'scheduled')
        """,
        (name, phone, doctor, date, time)
    )

    db.commit()
    return f"✅ Appointment booked for {name} with Dr. {doctor} on {date} at {time}."
