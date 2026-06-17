from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- TYPES & DATA ---
class ChatMessage(BaseModel):
    message: str
    role: Optional[str] = "patient"      # patient | doctor | nurse | admin
    user_name: Optional[str] = None      # e.g. "Dr. Imran Khan" or "Nurse Fatima" (optional, for future login support)

# Live Mock Data
doctors = [
    {"id": 1, "name": "Dr. Imran Khan", "specialty": "Cardiology", "available": True, "slots": ["9:00 AM", "10:00 AM", "2:00 PM"]},
    {"id": 2, "name": "Dr. Sana Mirza", "specialty": "General Medicine", "available": True, "slots": ["11:00 AM", "3:00 PM"]},
    {"id": 3, "name": "Dr. Tariq Mehmood", "specialty": "Orthopedics", "available": True, "slots": ["10:00 AM", "4:00 PM"]},
    {"id": 4, "name": "Dr. Zara Ali", "specialty": "Pediatrics", "available": True, "slots": ["9:00 AM", "11:00 AM", "2:00 PM"]},
    {"id": 5, "name": "Dr. Bilal Akhtar", "specialty": "Surgery", "available": False, "slots": []},
    {"id": 6, "name": "Dr. Nadia Shah", "specialty": "Neurology", "available": True, "slots": ["3:00 PM"]},
    {"id": 7, "name": "Dr. Kamran Butt", "specialty": "Dermatology", "available": True, "slots": ["10:00 AM", "1:00 PM"]},
    {"id": 8, "name": "Dr. Farah Naz", "specialty": "Gynecology", "available": True, "slots": ["9:00 AM", "2:00 PM", "4:00 PM"]}
]

nurses = [
    {"id": 1, "name": "Nurse Fatima", "ward": "ICU", "shift": "Morning", "on_duty": True},
    {"id": 2, "name": "Nurse Zainab", "ward": "Pediatrics", "shift": "Night", "on_duty": True},
    {"id": 3, "name": "Nurse Ali", "ward": "Emergency", "shift": "Evening", "on_duty": False}
]

appointments = [
    {"id": 1, "patient": "Ahmad Ali", "doctor": "Dr. Imran Khan", "dept": "Cardiology", "time": "09:00 AM", "status": "waiting"},
    {"id": 2, "patient": "Sara Khan", "doctor": "Dr. Sana Mirza", "dept": "General Medicine", "time": "11:00 AM", "status": "completed"}
]

# --- HELPERS ---
def any_word(user_msg: str, words: list[str]) -> bool:
    """True if any of the given words/phrases appear in the message."""
    return any(w in user_msg for w in words)


def find_named_doctor(user_msg: str):
    for doc in doctors:
        if doc["name"].lower() in user_msg or doc["specialty"].lower() in user_msg:
            return doc
    return None


def find_named_nurse(user_msg: str):
    for nurse in nurses:
        if nurse["name"].lower() in user_msg or nurse["ward"].lower() in user_msg:
            return nurse
    return None


# --- ROLE-SPECIFIC CHAT HANDLERS ---

def handle_patient_chat(user_msg: str) -> str:
    # 1. Doctor availability requests
    if any_word(user_msg, ["doctor", "available", "who is free", "free today"]):
        available_list = [f"{d['name']} ({d['specialty']})" for d in doctors if d["available"]]
        return ("The doctors currently available at City Hospital are: "
                + ", ".join(available_list) + ". You can book an appointment using the form below!")

    # 2. Specific doctor / specialty queries
    doc = find_named_doctor(user_msg)
    if doc:
        if doc["available"]:
            slots_str = ", ".join(doc["slots"]) if doc["slots"] else "No slots remaining"
            return f"{doc['name']} ({doc['specialty']}) is available today! Their open slots are: {slots_str}."
        return f"I'm sorry, {doc['name']} is currently unavailable or off-duty today."

    # 3. Timings / visiting hours
    if any_word(user_msg, ["time", "hour", "visiting"]):
        return ("City Hospital's general visiting hours are from 9:00 AM to 8:00 PM daily. "
                "Specialized clinics operate based on scheduled doctor slots.")

    # 4. Appointment booking
    if any_word(user_msg, ["book", "appointment"]):
        return ("To book an appointment, simply fill out the 'Book Appointment' form on your dashboard panel, "
                "select an available slot, and submit.")

    return ("Hello! I am MediBot. I can help you check active doctor availability, look up clinic schedules, "
            "or assist you with hospital navigation info. What can I do for you?")


def handle_doctor_chat(user_msg: str, user_name: Optional[str]) -> str:
    # Try to scope to a specific doctor if we know who's asking, or if they named themselves
    doc = None
    if user_name:
        doc = next((d for d in doctors if d["name"].lower() == user_name.lower()), None)
    if not doc:
        doc = find_named_doctor(user_msg)

    # 1. Schedule / appointments / patient queue
    if any_word(user_msg, ["my schedule", "schedule", "my patients", "patient list", "appointments today", "queue", "who do i see"]):
        if doc:
            mine = [a for a in appointments if a["doctor"] == doc["name"]]
        else:
            mine = appointments
        if not mine:
            return "You have no appointments scheduled at the moment. Your queue is currently clear."
        lines = [f"{a['patient']} – {a['time']} ({a['status']})" for a in mine]
        return "Here is your current appointment queue: " + "; ".join(lines) + "."

    # 2. Availability status
    if any_word(user_msg, ["my availability", "am i available", "am i on duty", "my status"]):
        if doc:
            status = "marked as Available" if doc["available"] else "marked as Unavailable"
            return f"You are currently {status}. You can toggle this from the Admin panel if it needs to change."
        return "I can check doctor availability status — could you tell me your name (e.g. 'Dr. Imran Khan')?"

    # 3. Pending lab results / general patient lookup (not in current data model, give an honest answer)
    if any_word(user_msg, ["lab result", "lab report", "test result"]):
        return ("Lab results aren't tracked in this system yet. Right now I can show your appointment queue, "
                "availability status, and hospital-wide doctor/nurse info.")

    # 4. Nurse / staff on duty
    if any_word(user_msg, ["nurse on duty", "nurses available", "who is on duty"]):
        on_duty = [n["name"] for n in nurses if n["on_duty"]]
        return "Nurses currently on duty: " + (", ".join(on_duty) if on_duty else "none right now") + "."

    # 5. Hospital-wide doctor availability (useful for referrals)
    if any_word(user_msg, ["available doctors", "other doctors", "who else is free"]):
        available_list = [f"{d['name']} ({d['specialty']})" for d in doctors if d["available"]]
        return "Doctors currently available: " + ", ".join(available_list) + "."

    return ("Hello Doctor! I can show your appointment queue, your availability status, "
            "or general hospital staffing info. Try asking 'show my schedule' or 'am I available today'.")


def handle_nurse_chat(user_msg: str, user_name: Optional[str]) -> str:
    nurse = None
    if user_name:
        nurse = next((n for n in nurses if n["name"].lower() == user_name.lower()), None)
    if not nurse:
        nurse = find_named_nurse(user_msg)

    # 1. Shift queries
    if any_word(user_msg, ["my shift", "next shift", "shift", "working today", "my hours"]):
        if nurse:
            duty = "on duty" if nurse["on_duty"] else "off duty"
            return f"You are assigned to the {nurse['ward']} ward, {nurse['shift']} shift, and are currently {duty}."
        return "I can check shift info — could you tell me your name (e.g. 'Nurse Fatima')?"

    # 2. Ward / duty status of staff
    if any_word(user_msg, ["who is on duty", "on duty", "staff on duty"]):
        on_duty = [f"{n['name']} ({n['ward']})" for n in nurses if n["on_duty"]]
        return "Currently on duty: " + (", ".join(on_duty) if on_duty else "no one right now") + "."

    # 3. Ward-specific lookup
    if any_word(user_msg, ["icu", "pediatrics", "emergency", "ward"]):
        matches = [n for n in nurses if n["ward"].lower() in user_msg or "ward" in user_msg]
        if matches:
            lines = [f"{n['name']} – {n['shift']} shift ({'On Duty' if n['on_duty'] else 'Off Duty'})" for n in matches]
            return "Ward assignments: " + "; ".join(lines) + "."

    # 4. Checklist / tasks (not in current data model, be honest)
    if any_word(user_msg, ["checklist", "task", "vitals", "sync data"]):
        return ("Your shift checklist is shown on the dashboard panel. I don't have item-level detail wired up yet, "
                "but I can tell you your ward, shift, and duty status.")

    # 5. Doctor availability (nurses often need this too)
    if any_word(user_msg, ["doctor available", "which doctor", "doctor on duty"]):
        available_list = [f"{d['name']} ({d['specialty']})" for d in doctors if d["available"]]
        return "Doctors currently available: " + ", ".join(available_list) + "."

    return ("Hi Nurse! I can tell you your shift, ward assignment, duty status, or which staff are on duty. "
            "Try asking 'my next shift' or 'who is on duty'.")


def handle_admin_chat(user_msg: str) -> str:
    total_appts = len(appointments)
    doctors_on = sum(1 for d in doctors if d["available"])
    nurses_on = sum(1 for n in nurses if n["on_duty"])

    # 1. Today's summary / overview
    if any_word(user_msg, ["today's summary", "summary", "overview", "stats", "report"]):
        return (f"Today's summary: {total_appts} total appointments, {doctors_on} doctors on duty, "
                f"{nurses_on} nurses on duty, and bed occupancy at 68%.")

    # 2. Doctors on duty
    if any_word(user_msg, ["doctors on duty", "how many doctors", "doctor count"]):
        names = [d["name"] for d in doctors if d["available"]]
        return f"{doctors_on} doctors are currently on duty: " + ", ".join(names) + "."

    # 3. Nurses on duty
    if any_word(user_msg, ["nurses on duty", "how many nurses", "nurse count"]):
        names = [n["name"] for n in nurses if n["on_duty"]]
        return f"{nurses_on} nurses are currently on duty: " + ", ".join(names) + "."

    # 4. Appointments / queue
    if any_word(user_msg, ["appointment", "queue", "waiting", "completed"]):
        waiting = [a for a in appointments if a["status"] == "waiting"]
        completed = [a for a in appointments if a["status"] == "completed"]
        return f"There are {len(appointments)} total appointments today: {len(waiting)} waiting, {len(completed)} completed."

    # 5. Bed occupancy
    if any_word(user_msg, ["bed", "occupancy"]):
        return "Current bed occupancy is at 68%."

    return ("Good day, Admin! I can give you today's summary, doctor/nurse duty counts, appointment status, "
            "or bed occupancy. Try asking 'today's summary'.")


# --- ENDPOINTS ---
@app.get("/")
def home():
    return {"status": "✅ MediBot API is running", "version": "1.1.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/doctors")
def get_doctors():
    return {"doctors": doctors}

@app.put("/doctors/{doctor_id}/availability")
def toggle_availability(doctor_id: int, payload: dict):
    for doc in doctors:
        if doc["id"] == doctor_id:
            doc["available"] = payload.get("available", doc["available"])
            return {"success": True, "doctor": doc}
    return {"error": "Doctor not found"}

@app.get("/nurses")
def get_nurses():
    return {"nurses": nurses}

@app.get("/appointments")
def get_appointments():
    return {"appointments": appointments}

@app.get("/admin/overview")
def get_overview():
    return {
        "total_appointments": len(appointments),
        "doctors_on_duty": sum(1 for d in doctors if d["available"]),
        "nurses_on_duty": sum(1 for n in nurses if n["on_duty"]),
        "bed_occupancy_percent": 68
    }

@app.post("/appointments/book")
def book_appointment(data: dict):
    new_id = len(appointments) + 1
    conf_id = f"MB{1000 + new_id}"
    new_appt = {
        "id": new_id,
        "patient": data.get("patient_name"),
        "doctor": data.get("doctor"),
        "dept": data.get("department"),
        "time": data.get("time"),
        "status": "waiting"
    }
    appointments.append(new_appt)
    return {"success": True, "confirmation_id": conf_id}

# --- ROLE-AWARE, RULE-BASED CHAT ENDPOINT (free, no external API) ---
@app.post("/chat/ai")
async def ai_chat(msg: ChatMessage):
    user_msg = msg.message.lower()
    role = (msg.role or "patient").lower()

    if role == "doctor":
        reply = handle_doctor_chat(user_msg, msg.user_name)
    elif role == "nurse":
        reply = handle_nurse_chat(user_msg, msg.user_name)
    elif role == "admin":
        reply = handle_admin_chat(user_msg)
    else:
        reply = handle_patient_chat(user_msg)

    return {"reply": reply}