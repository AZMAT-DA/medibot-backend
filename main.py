from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
    role: str

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

# --- ENDPOINTS ---
@app.get("/")
def home():
    return {"status": "✅ MediBot API is running", "version": "1.0.0"}

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

# --- ACCURATE, LOCAL INTELLIGENT EXPERT MATCHING ENDPOINT ---
@app.post("/chat/ai")
async def ai_chat(msg: ChatMessage):
    user_msg = msg.message.lower()
    
    # 1. Handle Doctor Availability Requests
    if "doctor" in user_msg or "available" in user_msg or "who is free" in user_msg:
        available_list = [f"{d['name']} ({d['specialty']})" for d in doctors if d["available"]]
        reply = "The doctors currently available at City Hospital are: " + ", ".join(available_list) + ". You can book an appointment using the form below!"
        return {"reply": reply}
        
    # 2. Specific Doctor Queries
    for doc in doctors:
        doc_name_lower = doc["name"].lower()
        if doc_name_lower in user_msg or doc["specialty"].lower() in user_msg:
            if doc["available"]:
                slots_str = ", ".join(doc["slots"]) if doc["slots"] else "No slots remaining"
                return {"reply": f"{doc['name']} ({doc['specialty']}) is available today! Their open slots are: {slots_str}."}
            else:
                return {"reply": f"Im sorry, {doc['name']} is currently unavailable or off-duty today."}
                
    # 3. Handle Timings / Visiting hours
    if "time" in user_msg or "hour" in user_msg or "visiting" in user_msg:
        return {"reply": "City Hospital's general visiting hours are from 9:00 AM to 8:00 PM daily. Specialized clinics operate based on scheduled doctor slots."}
        
    # 4. Handle Appointment queries
    if "book" in user_msg or "appointment" in user_msg:
        return {"reply": "To book an appointment, simply fill out the 'Book Appointment' form on your dashboard panel, select an available slot, and submit."}

    # Fallback generic helpful response
    return {"reply": "Hello! I am MediBot. I can help you check active doctor availability, look up clinic schedules, or assist you with hospital navigation info. What can I do for you?"}