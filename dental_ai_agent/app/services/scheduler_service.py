# app/services/scheduler_service.py

from apscheduler.schedulers.background import BackgroundScheduler
from app.db.connection import get_db
from app.services.reminder_service import make_reminder_call


def send_reminders():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM appointments
        WHERE appointment_date = CURDATE()
    """)

    appointments = cursor.fetchall()

    for appt in appointments:

        print(
            f"Calling {appt['patient_name']}"
        )

        make_reminder_call(
            appt["phone_number"],
            appt["id"]
        )


def start_scheduler():

    scheduler = BackgroundScheduler()

    scheduler.add_job(
        send_reminders,
        "cron",
        hour=9,
        minute=0
    )

    scheduler.start()

    print("✅ Reminder Scheduler Started")