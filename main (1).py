from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="MediBot Backend API", version="1.0.0")

# ── CORS (allow your Vercel frontend + localhost) ──────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Replace "*" with your Vercel URL after deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════════════════
#  SAMPLE DATA  (replace with a real database in production)
# ═══════════════════════════════════════════════════════════════════════════════

DOCTORS = [
    {"id": 1, "name": "Dr. Imran Khan",    "specialty": "Cardiology",       "available": True,  "slots": ["9:00 AM","10:00 AM","2:00 PM"]},
    {"id": 2, "name": "Dr. Sana Mirza",    "specialty": "General Medicine",  "available": True,  "slots": ["11:00 AM","3:00 PM"]},
    {"id": 3, "name": "Dr. Tariq Mehmood", "specialty": "Orthopedics",      "available": True,  "slots": ["10:00 AM","4:00 PM"]},
    {"id": 4, "name": "Dr. Zara Ali",      "specialty": "Pediatrics",       "available": True,  "slots": ["9:00 AM","11:00 AM","2:00 PM"]},
    {"id": 5, "name": "Dr. Bilal Akhtar",  "specialty": "Surgery",          "available": False, "slots": []},
    {"id": 6, "name": "Dr. Nadia Shah",    "specialty": "Neurology",        "available": True,  "slots": ["3:00 PM"]},
    {"id": 7, "name": "Dr. Kamran Butt",   "specialty": "Dermatology",      "available": True,  "slots": ["10:00 AM","1:00 PM"]},
    {"id": 8, "name": "Dr. Farah Naz",     "specialty": "Gynecology",       "available": True,  "slots": ["9:00 AM","2:00 PM","4:00 PM"]},
]

APPOINTMENTS = [
    {"id": 1, "patient": "Aisha Raza",     "doctor": "Dr. Imran Khan",  "dept": "Cardiology",      "time": "9:00 AM",  "status": "completed"},
    {"id": 2, "patient": "Ahmed Siddiqui", "doctor": "Dr. Imran Khan",  "dept": "Cardiology",      "time": "10:00 AM", "status": "completed"},
    {"id": 3, "patient": "Fatima Baig",    "doctor": "Dr. Imran Khan",  "dept": "Cardiology",      "time": "11:30 AM", "status": "in_progress"},
    {"id": 4, "patient": "Sara Hassan",    "doctor": "Dr. Sana Mirza",  "dept": "General Medicine","time": "10:30 AM", "status": "waiting"},
    {"id": 5, "patient": "Kamran Butt",    "doctor": "Dr. Zara Ali",    "dept": "Pediatrics",      "time": "12:00 PM", "status": "waiting"},
    {"id": 6, "patient": "Rabia Nawaz",    "doctor": "Dr. Nadia Shah",  "dept": "Neurology",       "time": "2:00 PM",  "status": "scheduled"},
]

NURSES = [
    {"id": 1, "name": "Hina Malik",    "ward": "Ward 6A", "shift": "Morning (6AM-2PM)",   "on_duty": True},
    {"id": 2, "name": "Sadia Noor",    "ward": "Ward 4B", "shift": "Morning (6AM-2PM)",   "on_duty": True},
    {"id": 3, "name": "Rubina Akhtar", "ward": "ICU",     "shift": "Night (10PM-6AM)",    "on_duty": False},
    {"id": 4, "name": "Amna Sheikh",   "ward": "Ward 3C", "shift": "Evening (2PM-10PM)",  "on_duty": False},
]

# ═══════════════════════════════════════════════════════════════════════════════
#  REQUEST MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class AppointmentRequest(BaseModel):
    patient_name: str
    cnic: str
    department: str
    doctor: str
    date: str
    time: str
    reason: str
    phone: str

class ChatMessage(BaseModel):
    message: str
    role: str   # patient | doctor | nurse | admin

class DoctorAvailability(BaseModel):
    doctor_id: int
    available: bool

# ═══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {
        "status": "✅ MediBot API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

# ── DOCTORS ───────────────────────────────────────────────────────────────────

@app.get("/doctors")
def get_doctors():
    return {"doctors": DOCTORS}

@app.get("/doctors/available")
def get_available_doctors():
    available = [d for d in DOCTORS if d["available"]]
    return {"doctors": available, "count": len(available)}

@app.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: int):
    doc = next((d for d in DOCTORS if d["id"] == doctor_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doc

@app.put("/doctors/{doctor_id}/availability")
def update_doctor_availability(doctor_id: int, body: DoctorAvailability):
    doc = next((d for d in DOCTORS if d["id"] == doctor_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doc["available"] = body.available
    return {"message": "Availability updated", "doctor": doc}

# ── APPOINTMENTS ──────────────────────────────────────────────────────────────

@app.get("/appointments")
def get_all_appointments():
    return {"appointments": APPOINTMENTS, "total": len(APPOINTMENTS)}

@app.get("/appointments/stats")
def get_appointment_stats():
    total     = len(APPOINTMENTS)
    completed = len([a for a in APPOINTMENTS if a["status"] == "completed"])
    waiting   = len([a for a in APPOINTMENTS if a["status"] == "waiting"])
    scheduled = len([a for a in APPOINTMENTS if a["status"] == "scheduled"])
    return {
        "total": total,
        "completed": completed,
        "waiting": waiting,
        "scheduled": scheduled,
        "in_progress": len([a for a in APPOINTMENTS if a["status"] == "in_progress"]),
    }

@app.post("/appointments/book")
def book_appointment(req: AppointmentRequest):
    new_appt = {
        "id": len(APPOINTMENTS) + 1,
        "patient": req.patient_name,
        "doctor": req.doctor,
        "dept": req.department,
        "time": req.time,
        "date": req.date,
        "reason": req.reason,
        "phone": req.phone,
        "status": "scheduled",
    }
    APPOINTMENTS.append(new_appt)
    return {
        "message": "✅ Appointment booked successfully!",
        "appointment": new_appt,
        "confirmation_id": f"MB{new_appt['id']:04d}"
    }

@app.delete("/appointments/{appt_id}")
def cancel_appointment(appt_id: int):
    appt = next((a for a in APPOINTMENTS if a["id"] == appt_id), None)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt["status"] = "cancelled"
    return {"message": "Appointment cancelled", "id": appt_id}

# ── NURSES ────────────────────────────────────────────────────────────────────

@app.get("/nurses")
def get_nurses():
    return {"nurses": NURSES}

@app.get("/nurses/on-duty")
def get_nurses_on_duty():
    on_duty = [n for n in NURSES if n["on_duty"]]
    return {"nurses": on_duty, "count": len(on_duty)}

# ── CHAT ─────────────────────────────────────────────────────────────────────

@app.post("/chat")
def chat(msg: ChatMessage):
    """
    Simple rule-based chatbot.
    In Step 3 you will replace this with a real AI API call.
    """
    text  = msg.message.lower()
    role  = msg.role

    # Patient responses
    if role == "patient":
        if any(w in text for w in ["doctor", "cardiolog", "general", "available"]):
            avail = [d["name"] for d in DOCTORS if d["available"]]
            return {"reply": f"Available doctors right now: {', '.join(avail)}. Would you like to book one?"}
        if any(w in text for w in ["book", "appointment", "schedule"]):
            return {"reply": "To book an appointment, go to 'Book Appointment' in the menu. You can choose your doctor, date and time slot."}
        if any(w in text for w in ["visiting", "hours", "visit"]):
            return {"reply": "Visiting hours:\n🕐 Morning: 10:00 AM – 12:00 PM\n🕐 Evening: 5:00 PM – 7:00 PM"}

    # Doctor responses
    if role == "doctor":
        if any(w in text for w in ["schedule", "appointment", "today"]):
            today = [a for a in APPOINTMENTS if a["status"] in ["waiting","in_progress","scheduled"]]
            return {"reply": f"You have {len(today)} appointments today. Check 'Today's Schedule' for details."}

    # Nurse responses
    if role == "nurse":
        if any(w in text for w in ["shift", "duty", "ward"]):
            return {"reply": "Your current shift: Morning — Ward 6A (6:00 AM – 2:00 PM). Check 'My Shifts' for full schedule."}

    # Admin responses
    if role == "admin":
        if any(w in text for w in ["report", "stats", "summary"]):
            stats = get_appointment_stats()
            return {"reply": f"Today: {stats['total']} total appointments — {stats['completed']} done, {stats['waiting']} waiting, {stats['scheduled']} scheduled."}

    # Fallback
    return {"reply": "I understand your query. Could you provide more detail so I can assist better? For urgent matters please contact ext. 100."}

# ── ADMIN OVERVIEW ────────────────────────────────────────────────────────────

@app.get("/admin/overview")
def admin_overview():
    return {
        "total_appointments": len(APPOINTMENTS),
        "doctors_on_duty": len([d for d in DOCTORS if d["available"]]),
        "nurses_on_duty": len([n for n in NURSES if n["on_duty"]]),
        "bed_occupancy_percent": 74,
        "appointment_stats": get_appointment_stats(),
    }

# ═══════════════════════════════════════════════════════════════════════════════
#  RUN (for local dev only — Hugging Face uses the CMD in Dockerfile)
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7860, reload=True)
