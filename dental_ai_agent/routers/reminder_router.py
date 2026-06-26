# app/routers/reminder_router.py

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.voice_response import VoiceResponse, Gather

from app.db.connection import get_db

router = APIRouter()

REMINDER_SESSIONS = {}