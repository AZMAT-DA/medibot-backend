import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import anthropic
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

# Role-specific Intelligent Prompts for Claude
SYSTEM_PROMPTS = {
    "patient": """You are MediBot, an empathetic hospital AI assistant for PATIENTS at City Hospital Pakistan. 
Help with: general inquiries, navigating visiting hours (10AM-12PM, 5PM-7PM), and clarifying available services.
Guidelines: Be warm, polite, and clear. Keep answers to 2-4 sentences. 
CRITICAL: Never provide definitive medical diagnoses or prescribe medications. If symptoms sound urgent (e.g., severe chest pain, breathing difficulties), direct them immediately to the Emergency Room (Ext. 100).""",
    
    "doctor": """You are MediBot, a clinical workflow assistant for DOCTORS at City Hospital Pakistan. 
Help with: standard medical terminology lookups, formatting administrative shift summaries, and providing brief, clinical updates. 
Guidelines: Be highly professional, accurate, and concise. Respect their medical expertise.""",
    
    "nurse": """You are MediBot, an operational coordination assistant for NURSES at City Hospital Pakistan. 
Help with: shift handovers, looking up ward layouts, and standard nursing checklists. 
Guidelines: Be practical, task-focused, supportive, and efficient.""",
    
    "admin": """You are MediBot, an operational intelligence assistant for ADMINS at City Hospital Pakistan. 
Help with: generating daily metrics summaries, template reports, and drafting administrative announcements.
Guidelines: Be factual, data-driven, precise, and analytical."""
}

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

# ── CLAUDE AI CHAT ────────────────────────────────────────────────────────────

@app.post("/chat/ai")
async def ai_chat(msg: ChatMessage):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"reply": "System Error: Backend ANTHROPIC_API_KEY secret is missing. Please add it to Hugging Face settings."}
        
    try:
        # Build contextual awareness regarding the hospital's live data
        live_context = f"\n\nLive Database Context:\n"
        live_context += f"- Active Doctors: {', '.join([d['name'] + ' (' + d['specialty'] + ')' for d in DOCTORS if d['available']])}\n"
        live_context += f"- Current Appointments Booked Today: {len(APPOINTMENTS)}\n"
        live_context += f"- Nurses Currently On Duty: {', '.join([n['name'] + ' (' + n['ward'] + ')' for n in NURSES if n['on_duty']])}"

        client = anthropic.Anthropic(api_key=api_key)
        system_context = SYSTEM_PROMPTS.get(msg.role.lower(), SYSTEM_PROMPTS["patient"]) + live_context
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=400,
            temperature=0.5,
            system=system_context,
            messages=[
                {"role": "user", "content": msg.message}
            ]
        )
        return {"reply": message.content[0].text}
    except Exception as e:
        return {"reply": f"I am experiencing difficulty rendering a response right now. (Error: {str(e)})"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7860, reload=True)
    # rebuild