from langchain.tools import tool
from app.db.connection import get_db


@tool
def reschedule_slot(appointment_id: int, new_date: str, new_time: str) -> str:
    """
    Reschedule an appointment
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE appointments
        SET date=%s, time=%s, status='rescheduled'
        WHERE appointment_id=%s
        """,
        (new_date, new_time, appointment_id)
    )

    db.commit()
    return f"🔄 Appointment {appointment_id} rescheduled to {new_date} at {new_time}."
