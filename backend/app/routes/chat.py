from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import google.generativeai as genai
from typing import List, Optional

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []

@router.post("")
async def chat_response(request: ChatRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"response": "System Error: Gemini API key not configured."}

    genai.configure(api_key=api_key)

    system_instruction = (
        "You are the East Blue Neural Assistant, an elite fitness AI. "
        "You give elite fitness advice, promote the gym's classes, and speak with high energy. "
        "Keep your responses concise, punchy, and highly motivating. Use terms like 'Elite', 'Optimal', and 'Neural Assessment'."
    )

    try:
        # We use the gemini-flash-lite-latest model for the highest possible free-tier quota
        model = genai.GenerativeModel('gemini-flash-lite-latest', system_instruction=system_instruction)
        
        # Convert history format
        formatted_history = []
        for msg in request.history:
            role = "user" if msg.get("role") == "user" else "model"
            formatted_history.append({"role": role, "parts": [msg.get("text")]})
            
        chat_session = model.start_chat(history=formatted_history)
        response = chat_session.send_message(request.message)
        
        return {"response": response.text}
    except Exception as e:
        print(f"Gemini API Error: {e}", flush=True)
        return {"response": "Neural Link offline. Unable to reach the AI core. Try again later."}
