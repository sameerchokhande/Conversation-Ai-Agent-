from app.db.connection import get_db
from langchain.tools import tool

# ===============================
# FASTAPI / DB FUNCTION
# ===============================
def cancel_slot_db(appointment_id: int) -> str:
    """
    Cancel an appointment (DB version for FastAPI)
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE appointments
        SET status='cancelled'
        WHERE id=%s
        """,
        (appointment_id,)
    )

    if cursor.rowcount == 0:
        return "No active appointment found to cancel."

    db.commit()
    return "Your appointment has been cancelled successfully."


# ===============================
# LANGCHAIN TOOL (AI USE ONLY)
# ===============================
@tool
def cancel_slot(appointment_id: int) -> str:
    """
    Cancel an appointment
    """
    return cancel_slot_db(appointment_id)
