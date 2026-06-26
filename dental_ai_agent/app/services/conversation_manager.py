from app.services.nlp_processor import extract_appointment_data

CALL_SESSIONS = {}

# ✅ Match EXACT fields from NLP
FIELDS = [
    "patient_name",
    "address",
    "reason",
    "doctor_name",
    "appointment_date",
    "appointment_time"
]


def get_missing_field(data):
    """
    Find the next missing field
    """
    for field in FIELDS:
        if not data.get(field):
            return field
    return "confirm"


def update_session(call_id, user_input):
    """
    Update conversation session using AI-extracted data
    """

    # Get existing session or create new
    session = CALL_SESSIONS.get(call_id, {
        "data": {},
        "step": "patient_name"
    })

    # 🔥 Extract using your Gemini NLP (multilingual)
    extracted = extract_appointment_data(user_input)

    if extracted:
        # Merge only non-empty values
        for key, value in extracted.items():
            if value:
                session["data"][key] = value

    # Determine next step dynamically
    next_step = get_missing_field(session["data"])
    session["step"] = next_step

    # Save session
    CALL_SESSIONS[call_id] = session

    return session