from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime, date
from typing import Optional
import os

from app.db.connection import get_db

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER", "+18666883811")

@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "twilio_phone": TWILIO_PHONE}
    )

@router.get("/appointments", response_class=HTMLResponse)
async def appointments_page(request: Request):
    return templates.TemplateResponse(
        "appointments.html",
        {"request": request}
    )

@router.get("/api/appointments")
async def get_appointments(
    search: Optional[str] = Query(None),
    doctor: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort: str = Query("desc")
):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    conditions = []
    params = []

    if search:
        conditions.append("(patient_name LIKE %s OR reason LIKE %s)")
        like = f"%{search}%"
        params.extend([like, like])

    if doctor:
        conditions.append("doctor_name = %s")
        params.append(doctor)

    if status:
        conditions.append("status = %s")
        params.append(status)

    if date_from:
        conditions.append("appointment_date >= %s")
        params.append(date_from)

    if date_to:
        conditions.append("appointment_date <= %s")
        params.append(date_to)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    count_query = f"SELECT COUNT(*) as total FROM appointments WHERE {where_clause}"
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]

    order = "DESC" if sort == "desc" else "ASC"
    offset = (page - 1) * limit
    data_query = f"""
        SELECT id, call_sid, patient_name, address, reason,
               doctor_name, appointment_date, appointment_time, status
        FROM appointments
        WHERE {where_clause}
        ORDER BY appointment_date {order}, appointment_time {order}
        LIMIT %s OFFSET %s
    """
    cursor.execute(data_query, params + [limit, offset])
    rows = cursor.fetchall()
    cursor.close()
    db.close()

    for row in rows:
        if row.get("appointment_time"):
            try:
                t = datetime.strptime(str(row["appointment_time"]), "%H:%M")
                row["appointment_time"] = t.strftime("%I:%M %p")
            except:
                pass
        if row.get("appointment_date") and isinstance(row["appointment_date"], date):
            row["appointment_date"] = row["appointment_date"].isoformat()

    return JSONResponse({
        "data": rows,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": max(1, (total + limit - 1) // limit)
    })

@router.get("/api/doctors")
async def get_doctors():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT name FROM doctors ORDER BY name")
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return JSONResponse({"data": [r["name"] for r in rows]})

@router.get("/api/appointments/stats")
async def get_appointment_stats():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    today = date.today().isoformat()

    cursor.execute("SELECT COUNT(*) as total FROM appointments")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM appointments WHERE appointment_date = %s", (today,))
    today_count = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM appointments WHERE status = 'scheduled'")
    pending = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM appointments WHERE status = 'completed'")
    completed = cursor.fetchone()["total"]

    cursor.close()
    db.close()

    return JSONResponse({
        "total": total,
        "today": today_count,
        "pending": pending,
        "completed": completed
    })

@router.put("/api/appointments/{appointment_id}")
async def update_appointment(appointment_id: int, request: Request):
    body = await request.json()
    db = get_db()
    cursor = db.cursor()

    allowed_fields = {"patient_name", "address", "reason",
                      "doctor_name", "appointment_date", "appointment_time", "status"}
    updates = []
    params = []

    for key, value in body.items():
        if key in allowed_fields:
            updates.append(f"{key} = %s")
            params.append(value)

    if not updates:
        cursor.close()
        db.close()
        raise HTTPException(status_code=400, detail="No valid fields to update")

    params.append(appointment_id)
    query = f"UPDATE appointments SET {', '.join(updates)} WHERE id = %s"
    cursor.execute(query, params)
    db.commit()
    affected = cursor.rowcount
    cursor.close()
    db.close()

    if affected == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return JSONResponse({"message": "Appointment updated successfully"})

@router.delete("/api/appointments/{appointment_id}")
async def delete_appointment(appointment_id: int):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM appointments WHERE id = %s", (appointment_id,))
    db.commit()
    affected = cursor.rowcount
    cursor.close()
    db.close()

    if affected == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return JSONResponse({"message": "Appointment deleted successfully"})
