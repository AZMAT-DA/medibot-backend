from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="MediBot Backend API", version="1.0.0")

# ── CORS — allow ALL origins (fixes the 0s issue) ─────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════════════════
#  DATA
# ═══════════════════════════════════════════════════════════════════════════════

DOCTORS = [
    {"id": 1, "name": "Dr. Imran Khan",    "specialty": "Cardiology",       "available": True,  "slots": ["9:00 AM", "10:00 AM", "2:00 PM"]},
    {"id": 2, "name": "Dr. Sana Mirza",    "specialty": "General Medicine",  "available": True,  "slots": ["11:00 AM", "3:00 PM"]},
    {"id": 3, "name": "Dr. Tariq Mehmood", "specialty": "Orthopedics",      "available": True,  "slots": ["10:00 AM", "4:00 PM"]},
    {"id": 4, "name": "Dr. Zara Ali",      "specialty": "Pediatrics",       "available": True,  "slots": ["9:00 AM", "11:00 AM", "2:00 PM"]},
    {"id": 5, "name": "Dr. Bilal Akhtar",  "specialty": "Surgery",          "available": False, "slots": []},
    {"id": 6, "name": "Dr. Nadia Shah",    "specialty": "Neurology",        "available": True,  "slots": ["3:00 PM"]},
    {"id": 7, "name": "Dr. Kamran Butt",   "specialty": "Dermatology",      "available": True,  "slots": ["10:00 AM", "1:00 PM"]},
    {"id": 8, "name": "Dr. Farah Naz",     "specialty": "Gynecology",       "available": True,  "slots": ["9:00 AM", "2:00 PM", "4:00 PM"]},
]

APPOINTMENTS = [
    {"id": 1, "patient": "Aisha Raza",     "doctor": "Dr. Imran Khan", "dept": "Cardiology",      "time": "9:00 AM",  "status": "completed"},
    {"id": 2, "patient": "Ahmed Siddiqui", "doctor": "Dr. Imran Khan", "dept": "Cardiology",      "time": "10:00 AM", "status": "completed"},
    {"id": 3, "patient": "Fatima Baig",    "doctor": "Dr. Imran Khan", "dept": "Cardiology",      "time": "11:30 AM", "status": "in_progress"},
    {"id": 4, "patient": "Sara Hassan",    "doctor": "Dr. Sana Mirza", "dept": "General Medicine","time": "10:30 AM", "status": "waiting"},
    {"id": 5, "patient": "Kamran Butt",    "doctor": "Dr. Zara Ali",   "dept": "Pediatrics",      "time": "12:00 PM", "status": "waiting"},
    {"id": 6, "patient": "Rabia Nawaz",    "doctor": "Dr. Nadia Shah", "dept": "Neurology",       "time": "2:00 PM",  "status": "scheduled"},
]

NURSES = [
    {"id": 1, "name": "Hina Malik",    "ward": "Ward 6A", "shift": "Morning (6AM-2PM)",  "on_duty": True},
    {"id": 2, "name": "Sadia Noor",    "ward": "Ward 4B", "shift": "Morning (6AM-2PM)",  "on_duty": True},
    {"id": 3, "name": "Rubina Akhtar", "ward": "ICU",     "shift": "Night (10PM-6AM)",   "on_duty": False},
    {"id": 4, "name": "Amna Sheikh",   "ward": "Ward 3C", "shift": "Evening (2PM-10PM)", "on_duty": False},
]

# ═══════════════════════════════════════════════════════════════════════════════
#  MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class AppointmentRequest(BaseModel):
    patient_name: str
    cnic: Optional[str] = "N/A"
    department: Optional[str] = "General"
    doctor: str
    date: str
    time: str
    reason: Optional[str] = "General consultation"
    phone: Optional[str] = "N/A"

class ChatMessage(BaseModel):
    message: str
    role: str

class DoctorAvailability(BaseModel):
    doctor_id: int
    available: bool

# ═══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {"status": "✅ MediBot API is running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# ── DOCTORS ───────────────────────────────────────────────────────────────────

@app.get("/doctors")
def get_doctors():
    return {"doctors": DOCTORS, "total": len(DOCTORS)}

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
def update_availability(doctor_id: int, body: DoctorAvailability):
    doc = next((d for d in DOCTORS if d["id"] == doctor_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doc["available"] = body.available
    return {"message": "Updated", "doctor": doc}

# ── APPOINTMENTS ──────────────────────────────────────────────────────────────

@app.get("/appointments")
def get_appointments():
    return {"appointments": APPOINTMENTS, "total": len(APPOINTMENTS)}

@app.get("/appointments/stats")
def get_stats():
    return {
        "total":       len(APPOINTMENTS),
        "completed":   len([a for a in APPOINTMENTS if a["status"] == "completed"]),
        "waiting":     len([a for a in APPOINTMENTS if a["status"] == "waiting"]),
        "scheduled":   len([a for a in APPOINTMENTS if a["status"] == "scheduled"]),
        "in_progress": len([a for a in APPOINTMENTS if a["status"] == "in_progress"]),
    }

@app.post("/appointments/book")
def book(req: AppointmentRequest):
    new_id = len(APPOINTMENTS) + 1
    appt = {
        "id": new_id, "patient": req.patient_name,
        "doctor": req.doctor, "dept": req.department,
        "time": req.time, "date": req.date,
        "reason": req.reason, "status": "scheduled",
    }
    APPOINTMENTS.append(appt)
    return {
        "message": "✅ Appointment booked!",
        "appointment": appt,
        "confirmation_id": f"MB{new_id:04d}"
    }

@app.delete("/appointments/{appt_id}")
def cancel(appt_id: int):
    appt = next((a for a in APPOINTMENTS if a["id"] == appt_id), None)
    if not appt:
        raise HTTPException(status_code=404, detail="Not found")
    appt["status"] = "cancelled"
    return {"message": "Cancelled", "id": appt_id}

# ── NURSES ────────────────────────────────────────────────────────────────────

@app.get("/nurses")
def get_nurses():
    return {"nurses": NURSES, "total": len(NURSES)}

@app.get("/nurses/on-duty")
def on_duty():
    active = [n for n in NURSES if n["on_duty"]]
    return {"nurses": active, "count": len(active)}

# ── ADMIN ─────────────────────────────────────────────────────────────────────

@app.get("/admin/overview")
def overview():
    return {
        "total_appointments":    len(APPOINTMENTS),
        "doctors_on_duty":       len([d for d in DOCTORS if d["available"]]),
        "nurses_on_duty":        len([n for n in NURSES if n["on_duty"]]),
        "bed_occupancy_percent": 74,
        "appointment_stats":     get_stats(),
    }

# ── CHAT ─────────────────────────────────────────────────────────────────────

@app.post("/chat")
def chat(msg: ChatMessage):
    t    = msg.message.lower()
    role = msg.role

    if role == "patient":
        if any(w in t for w in ["available", "doctor", "find", "cardiolog", "general", "specialist"]):
            avail = [d["name"] + " (" + d["specialty"] + ")" for d in DOCTORS if d["available"]]
            return {"reply": "Available doctors right now:\n\n" + "\n".join(f"✅ {a}" for a in avail) + "\n\nWould you like to book with any of them?"}
        if any(w in t for w in ["book", "appointment", "schedule"]):
            return {"reply": "To book an appointment, fill in the **Book Appointment** form on the right. Choose a doctor, date, and time slot, then click Confirm!"}
        if any(w in t for w in ["visiting", "hours", "visit", "time"]):
            return {"reply": "Visiting Hours:\n🕐 Morning: 10:00 AM – 12:00 PM\n🕐 Evening: 5:00 PM – 7:00 PM\n\nICU and pediatric wards may have different timings."}

    if role == "doctor":
        if any(w in t for w in ["schedule", "appointment", "today", "queue"]):
            pending = [a for a in APPOINTMENTS if a["status"] in ["waiting", "in_progress", "scheduled"]]
            return {"reply": f"You have **{len(pending)} pending appointments** today.\n\n" + "\n".join(f"• {a['patient']} at {a['time']} ({a['status']})" for a in pending)}
        if any(w in t for w in ["lab", "result", "test"]):
            return {"reply": "Pending lab results:\n🧪 Ahmed Raza — Blood panel (since yesterday)\n🧪 Nadia Iqbal — CBC results (urgent)\n\nShall I notify the lab to expedite?"}

    if role == "nurse":
        if any(w in t for w in ["shift", "duty", "ward", "next"]):
            on = [n for n in NURSES if n["on_duty"]]
            return {"reply": "Currently on duty:\n\n" + "\n".join(f"• {n['name']} — {n['ward']} ({n['shift']})" for n in on)}
        if any(w in t for w in ["task", "checklist", "todo"]):
            return {"reply": "Your pending tasks:\n☐ Administer medication — Room 6A-1 (by 12 PM)\n☐ Vitals check — Rooms 5, 6, 7\n☐ Prepare Room 8 for new admission\n✅ Morning rounds — Done"}
        if any(w in t for w in ["on-call", "on call", "oncall", "doctor"]):
            return {"reply": "On-call doctor right now:\n👨‍⚕️ Dr. Bilal Akhtar — General Surgery\n📞 Ext: 2234\n\nFor emergencies also page the ICU attending."}

    if role == "admin":
        if any(w in t for w in ["summary", "report", "stats", "today", "overview"]):
            s = get_stats()
            return {"reply": f"Today's Summary:\n📊 Total: {s['total']} | ✅ Done: {s['completed']} | 🕐 Waiting: {s['waiting']} | 📅 Scheduled: {s['scheduled']}\n\nDoctors on duty: {len([d for d in DOCTORS if d['available']])} | Nurses active: {len([n for n in NURSES if n['on_duty']])}"}
        if any(w in t for w in ["unavailable", "mark", "toggle"]):
            return {"reply": "To mark a doctor unavailable, scroll down to **Doctor Availability Control** and click the green button next to their name. Changes save to the backend instantly!"}

    fallbacks = [
        "I can help with appointments, doctor availability, schedules, and more. What do you need?",
        "For urgent matters, please contact the front desk at ext. 100.",
        "Could you provide more detail? I want to make sure I give you the right information.",
    ]
    import random
    return {"reply": random.choice(fallbacks)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7860, reload=True)