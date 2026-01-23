from langchain.tools import tool
from app.db.connection import get_db


@tool
def cancel_slot(appointment_id: int) -> str:
    """
    Cancel an appointment
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE appointments SET status='cancelled' WHERE appointment_id=%s",
        (appointment_id,)
    )

    db.commit()
    return f"❌ Appointment {appointment_id} cancelled successfully."
