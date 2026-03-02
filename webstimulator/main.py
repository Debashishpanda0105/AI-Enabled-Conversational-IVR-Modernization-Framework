from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- DATA MODELS --------

class StartCallRequest(BaseModel):
    caller_number: str = "Web Simulator"

class InputRequest(BaseModel):
    session_id: str
    digit: str
    current_menu: str

# -------- SESSION STORAGE --------

sessions = {}

# -------- MENU DEFINITIONS --------

MENUS = {
    "main": {
        "prompt": "Welcome to IRCTC. Press 1 for Booking, 2 for PNR Status.",
        "options": {
            "1": {"action": "goto", "target": "booking"},
            "2": {"action": "goto", "target": "status"}
        }
    },
    "booking": {
        "prompt": "Press 1 for Domestic Ticket, 2 for International Ticket.",
        "options": {
            "1": {"action": "end", "message": "Domestic booking selected. Thank you."},
            "2": {"action": "end", "message": "International booking selected. Thank you."}
        }
    },
    "status": {
        "prompt": "Enter your PNR later. For now press 0 to return to main menu.",
        "options": {
            "0": {"action": "goto", "target": "main"}
        }
    }
}

# -------- START CALL --------

@app.post("/ivr/start")
def start_call(request: StartCallRequest):
    session_id = f"SIM_{random.randint(100000, 999999)}"
    sessions[session_id] = {
        "current_menu": "main",
        "history": []
    }

    return {
        "session_id": session_id,
        "prompt": MENUS["main"]["prompt"],
        "menu": "main"
    }

# -------- HANDLE INPUT --------

@app.post("/ivr/input")
def handle_input(request: InputRequest):

    session = sessions.get(request.session_id)
    if not session:
        return {"error": "Session not found"}

    current_menu = session["current_menu"]
    menu = MENUS.get(current_menu)

    if request.digit not in menu["options"]:
        return {
            "status": "invalid",
            "prompt": menu["prompt"]
        }

    option = menu["options"][request.digit]

    if option["action"] == "goto":
        target = option["target"]
        session["current_menu"] = target

        return {
            "status": "ok",
            "menu": target,
            "prompt": MENUS[target]["prompt"]
        }

    elif option["action"] == "end":
        del sessions[request.session_id]

        return {
            "status": "hangup",
            "action": "hangup",
            "message": option["message"]
        }

@app.get("/")
def root():
    return {"status": "IVR Simulator Running"}
