from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

sessions = {}

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/ivr/start")
def start():
    session_id = f"SIM-{random.randint(1000, 9999)}"
    sessions[session_id] = {"state": "main_menu", "entities": {}}
    return {"session_id": session_id, "reply": "Namaste! Welcome to IRCTC. How can I assist you today?", "state": "main_menu"}

@app.post("/ivr/chat")
def chat(req: ChatRequest):
    session = sessions.get(req.session_id)
    msg = req.message.lower()
    
    # Default Debug Values
    confidence = random.randint(85, 98)
    entities = session.get("entities", {})

    if session["state"] == "main_menu":
        if "book" in msg or "1" in msg:
            session["state"] = "booking_origin"
            reply = "Great! Which city are you travelling FROM?"
        elif "pnr" in msg or "2" in msg:
            session["state"] = "pnr_wait"
            reply = "Please tell me your 10-digit PNR number."
        else:
            reply = "Sorry, I can help with Booking or PNR. What would you like?"
            confidence = 40

    elif session["state"] == "booking_origin":
        entities["origin"] = msg.capitalize()
        session["state"] = "booking_dest"
        reply = f"Noted. Travelling from {msg.capitalize()}. Where would you like to travel TO?"

    elif session["state"] == "booking_dest":
        entities["destination"] = msg.capitalize()
        session["state"] = "book_date"
        reply = f"Got it. What is your preferred date of travel?"

    elif session["state"] == "pnr_wait":
        entities["pnr_number"] = msg
        reply = f"Checking status for PNR {msg}... Your ticket is CONFIRMED."
        session["state"] = "main_menu"

    else:
        reply = "I'm processing your request. Please wait."

    return {
        "reply": reply,
        "state": session["state"],
        "confidence": confidence,
        "entities": entities
    }
