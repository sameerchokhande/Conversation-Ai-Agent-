from app.db.connection import get_db
from langchain.tools import tool

# ===============================
# FASTAPI / DB FUNCTION
# ===============================
def reschedule_slot_db(
    appointment_id: int,
    new_date: str,
    new_time: str
) -> str:
    """
    Reschedule an appointment (DB version for FastAPI)
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE appointments
        SET appointment_date=%s,
            appointment_time=%s,
            status='rescheduled'
        WHERE id=%s
        """,
        (new_date, new_time, appointment_id)
    )

    if cursor.rowcount == 0:
        return "No appointment found to reschedule."

    db.commit()
    return (
        f"Your appointment has been rescheduled to "
        f"{new_date} at {new_time}."
    )


# ===============================
# LANGCHAIN TOOL (AI USE ONLY)
# ===============================
@tool
def reschedule_slot(
    appointment_id: int,
    new_date: str,
    new_time: str
) -> str:
    """
    Reschedule an appointment
    """
    return reschedule_slot_db(appointment_id, new_date, new_time)
