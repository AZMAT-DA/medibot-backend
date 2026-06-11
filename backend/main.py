from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Allow your Next.js frontend to securely connect to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    role: str

@app.post("/api/chat")
async def hospital_chat(request: ChatRequest):
    user_query = request.message.lower()
    role = request.role
    
    # 1. PATIENT SMART ROUTING LOGIC
    if role == "patient":
        if "appoint" in user_query or "book" in user_query or "see a doctor" in user_query:
            return {"response": "To book an appointment immediately, please look at the calendar utility panel on the right side of your portal screen. Pick your preferred specialist, choose a time slot, and click 'Confirm Target Booking Slot'."}
        elif "cardio" in user_query or "heart" in user_query:
            return {"response": "Dr. Sarah Jenkins (Cardiology Specialist) is currently marked as 'Available'. You can submit an appointment query for her right now."}
        elif "emergency" in user_query or "pain" in user_query:
            return {"response": "⚠️ CRITICAL WARNING: If you are experiencing severe physical pain or a medical emergency, please do not wait for a chat response. Call emergency services (911) or proceed immediately to the nearest hospital ER."}
        else:
            return {"response": "Hello! I am your automated medical assistant. I can help guide you to available doctors, clarify hospital department hours, or assist you with booking standard appointments."}

    # 2. DOCTOR WORKFLOW LOGIC
    elif role == "doctor":
        if "schedule" in user_query or "appointment" in user_query or "today" in user_query:
            return {"response": "Roster Check: You have 3 consultations remaining on your schedule today. Your next check-in is Eleanor Vance at 11:15 AM for a Chronic Arrhythmia follow-up."}
        elif "surgery" in user_query or "op" in user_query:
            return {"response": "System Update: The afternoon surgical theatre block is confirmed. Patient pre-op vitals have been successfully synced to your terminal sidebar."}
        else:
            return {"response": "Physician Terminal online. You can ask me to parse your daily rounds roster, check patient check-in statuses, or log data verification summaries."}

    # 3. NURSE MATRIX LOGIC
    elif role == "nurse":
        if "shift" in user_query or "ward" in user_query:
            return {"response": "Shift Allocation: You are assigned to Ward A - Emergency for the Morning Shift (07:00 - 15:00). Jessica Taylor is scheduled to cover the oncoming Night sequence."}
        elif "check" in user_query or "task" in user_query:
            return {"response": "Task Sync: Please ensure the ICU vitals checklist is synced and the ER medication cart quota is verified before completing your shift log."}
        else:
            return {"response": "Nursing Hub online. Enter queries regarding active floor rotations, bed assignments, or station item compliance verification checklists."}

    # 4. SYSTEM ADMIN LOGIC
    elif role == "admin":
        if "status" in user_query or "system" in user_query or "health" in user_query:
            return {"response": "Infrastructure Status: Nominal. Database synchronization nodes are operating at 100% capacity. Zero performance latency anomalies detected."}
        elif "doctor" in user_query or "toggle" in user_query:
            return {"response": "Administrative Override: You can modify active personnel availability maps using the live resource toggle array on the right panel."}
        else:
            return {"response": "Root Administrative Command Line active. Monitor global infrastructure metrics or bypass active operational statuses natively."}

    return {"response": "I have received your log request in the system workspace. Let me know if you need specific help with hospital operations!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7860)