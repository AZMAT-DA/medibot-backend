from fastapi import FastAPI, HTTPException
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
    "patient": (
        "You are MediBot, a warm, polite, and highly intelligent hospital assistant for PATIENTS at City Hospital. "
        "Help them find doctors, understand schedules, or book appointments based on the hospital's actual data. "
        "Keep answers concise (2-3 sentences max). Never provide diagnostic or dangerous medical prescriptions. "
        "Always be helpful and natural."
    ),
    "doctor": (
        "You are MediBot, a professional medical executive assistant for DOCTORS. Help manage clinical workflows, "
        "schedules, and metrics using precise medical and operational terminology. Be direct and brief."
    ),
    "nurse": "You are MediBot, a practical workflow assistant for NURSES. Help organize ward duties, shifts, and tasks smoothly.",
    "admin": "You are MediBot, an analytical dashboard assistant for ADMINS. Provide summaries on hospital metrics like occupancy and staff allocation."
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

# --- SAFE CLIENT INITIALIZATION ---
HF_TOKEN = os.environ.get("HF_TOKEN")

# Explicit URL fallback initialization to fix NameResolutionError inside isolated containers
client = InferenceClient(
    model="https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct",
    token=HF_TOKEN
)

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

# --- ACCURATE & INTELLIGENT AI CHAT ENDPOINT ---
@app.post("/chat/ai")
async def ai_chat(msg: ChatMessage):
    try:
        # Determine the role context dynamically
        role_key = msg.role.lower() if msg.role else "patient"
        system_context = SYSTEM_PROMPTS.get(role_key, SYSTEM_PROMPTS["patient"])
        
        # Inject real-time backend data into the AI context for factual accuracy
        if role_key == "patient":
            available_docs = [f"{d['name']} ({d['specialty']})" for d in doctors if d["available"]]
            system_context += f" Current live available doctors at City Hospital right now: {', '.join(available_docs)}."
        elif role_key == "admin":
            system_context += f" Current Stats: Total appointments: {len(appointments)}, Bed Occupancy: 68%."

        # Payload structure expected by LLama-3 chat format
        messages = [
            {"role": "system", "content": system_context},
            {"role": "user", "content": msg.message}
        ]
        
        # Execute synchronous request to handle the JSON generation cleanly without stream mismatches
        completion = client.chat_completion(
            messages=messages,
            max_tokens=200,
            temperature=0.6,
            stream=False
        )
        
        response_text = completion.choices[0].message.content
        return {"reply": response_text.strip()}
        
    except Exception as e:
        # Returns the error directly to your frontend UI text window for quick adjustments
        return {"reply": f"System Alert: Chat processing error occurred. Details: {str(e)}"}