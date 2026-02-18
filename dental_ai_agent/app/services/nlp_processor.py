import google.generativeai as genai
import os
import json
import re
import dateparser

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def extract_appointment_data(raw_text: str):
    """
    Convert multilingual speech into structured English appointment data.
    """

    prompt = f"""
    Extract appointment information from this text:

    "{raw_text}"

    IMPORTANT RULES:
    - The user may speak in English, Hindi, or Marathi.
    - You MUST understand the meaning.
    - Return ALL fields translated into proper English.
    - Do NOT return Hindi or Marathi script.
    - Do NOT transliterate.
    - Convert to meaningful English words.

    Example:
    दातांची तपासणी → Dental checkup
    दात दुखत आहेत → Tooth pain
    दोन वाजता → 2:00 PM

    Return ONLY valid JSON in this format:

    {{
        "patient_name": "",
        "address": "",
        "reason": "",
        "doctor_name": "",
        "appointment_date": "",
        "appointment_time": ""
    }}
    """

    try:
        response = model.generate_content(prompt)
        raw_output = response.text.strip()

        print("\n🔎 RAW MODEL OUTPUT:")
        print(raw_output)

        raw_output = raw_output.replace("```json", "")
        raw_output = raw_output.replace("```", "").strip()

        match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if not match:
            print("❌ No JSON found")
            return None

        data = json.loads(match.group(0))

    except Exception as e:
        print("❌ JSON ERROR:", e)
        return None

    # -----------------------------
    # Normalize Date
    # -----------------------------
    if data.get("appointment_date"):
        parsed_date = dateparser.parse(
            data["appointment_date"],
            languages=["en", "hi", "mr"]
        )
        if parsed_date:
            data["appointment_date"] = parsed_date.strftime("%Y-%m-%d")

    # -----------------------------
    # Normalize Time
    # -----------------------------
    if data.get("appointment_time"):
        parsed_time = dateparser.parse(
            data["appointment_time"],
            languages=["en", "hi", "mr"]
        )
        if parsed_time:
            data["appointment_time"] = parsed_time.strftime("%H:%M")

    print("\n✅ FINAL STRUCTURED DATA:")
    print(data)

    return data
