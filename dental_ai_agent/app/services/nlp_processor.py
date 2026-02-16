import google.generativeai as genai
import os
import json
import dateparser

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")


def extract_appointment_data(raw_text: str):
    """
    Convert messy speech text into structured appointment data
    """

    prompt = f"""
    Extract appointment information from this text:

    "{raw_text}"

    Return ONLY JSON in this format:

    {{
        "patient_name": "",
        "address": "",
        "reason": "",
        "doctor_name": "",
        "appointment_date": "",
        "appointment_time": ""
    }}

    If something is missing, keep it empty.
    """

    response = model.generate_content(prompt)

    try:
        data = json.loads(response.text.strip())
    except:
        return None

    # Normalize date
    if data.get("appointment_date"):
        parsed_date = dateparser.parse(
            data["appointment_date"],
            languages=["en", "hi", "mr"]
        )
        if parsed_date:
            data["appointment_date"] = parsed_date.strftime("%Y-%m-%d")

    # Normalize time
    if data.get("appointment_time"):
        parsed_time = dateparser.parse(
            data["appointment_time"],
            languages=["en", "hi", "mr"]
        )
        if parsed_time:
            data["appointment_time"] = parsed_time.strftime("%H:%M")

    return data
