# api.py

from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from customer_support_agent import CustomerSupportAgent
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Enterprise Support AI API", version="2.0.0")
agent = CustomerSupportAgent()

# --- SECURITY ---
security = HTTPBearer()
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError(
        "API_KEY environment variable is not set. Refusing to start with no "
        "authentication configured — set API_KEY in your .env file."
    )

def validate_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized Access")
    return credentials.credentials

# --- MODELS ---
class ChatRequest(BaseModel):
    message: str
    state: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    state: Dict[str, Any]
    analytics: Dict[str, Any]

# --- ENDPOINTS ---
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, token: str = Depends(validate_api_key)):
    try:
        # 1. Initialize or Load State
        state = request.state if request.state else agent.start_conversation()
        
        # 2. Process Message
        updated_state = agent.send_message(state, request.message)
        
        # 3. Extract Response
        last_msg = updated_state["messages"][-1]
        content = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
        
        # 4. Compile Analytics
        analytics = {
            "tokens": updated_state.get("total_tokens", 0),
            "cost_usd": updated_state.get("total_tokens", 0) * 0.00000014,
            "active_specialist": updated_state.get("active_agent"),
            "is_human_needed": updated_state.get("is_human_takeover", False),
            "customer_tier": updated_state.get("customer_tier")
        }
        
        return ChatResponse(
            response=content,
            state=updated_state,
            analytics=analytics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine Error: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "operational", "version": "2.0.0", "db": "WAL-Active"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))
