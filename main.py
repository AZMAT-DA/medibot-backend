from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from huggingface_hub import InferenceClient

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

SYSTEM_PROMPTS = {
    "patient": "You are MediBot, a warm and helpful hospital assistant for PATIENTS at City Hospital. Help with appointments, finding doctors, and general symptoms. Keep answers to 2-3 sentences max. Never give dangerous medical advice.",
    "doctor": "You are MediBot, a professional hospital assistant for DOCTORS. Help with schedules, clinical records, and task lists briefly using medical terminology.",
    "nurse": "You are MediBot, a practical assistant for NURSES. Help organize ward duties, shift check-ins, and task workflows smoothly.",
    "admin": "You are MediBot, an analytical assistant for ADMINS. Provide summaries on hospital metrics like occupancy, appointments, and staff status."
}

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

@app.get("/appointments/stats")
def get_stats():
    return {
        "total": len(appointments),
        "completed": sum(1 for a in appointments if a["status"] == "completed"),
        "waiting": sum(1 for a in appointments if a["status"] == "waiting"),
        "scheduled": 0,
        "in_progress": 0
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

# --- FREE AI CHAT ENDPOINT ---
@app.post("/chat/ai")
async def ai_chat(msg: ChatMessage):
    try:
        hf_token = os.environ.get("HF_TOKEN")
        client = InferenceClient(
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            token=hf_token
        )
        
        system_context = SYSTEM_PROMPTS.get(msg.role, SYSTEM_PROMPTS["patient"])
        
        # Standard chat formatting structure
        messages = [
            {"role": "system", "content": system_context},
            {"role": "user", "content": msg.message}
        ]
        
        response = ""
        for message in client.chat_completion(
            messages,
            max_tokens=150,
            temperature=0.7,
            stream=True
        ):
            token = message.choices[0].delta.content
            if token:
                response += token
                
        return {"reply": response.strip()}
        
    except Exception as e:
        return {"reply": "Hello! I am ready to assist you. How can I help you today with our hospital management system?"}