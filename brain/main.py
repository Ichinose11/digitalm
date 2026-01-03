from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import os
import json

# Initialize App & Redis
app = FastAPI()
r = redis.Redis(host='redis', port=6379, decode_responses=True)

# Data Model (What n8n sends us)
class CampaignData(BaseModel):
    campaign_id: str
    cpa: float
    spend: float

@app.get("/")
def health_check():
    return {"status": "Brain is active"}

@app.post("/analyze")
def analyze_campaign(data: CampaignData):
    # 1. CHECK LOCKS (The "Nervous System")
    lock_key = f"lock:campaign:{data.campaign_id}"
    if r.exists(lock_key):
        return {"action": "skip", "reason": "Campaign is locked/optimizing"}

    # 2. SET LOCK (Prevent other agents from interfering)
    r.set(lock_key, "processing", ex=60) # Lock for 60 seconds

    # 3. LOGIC (Simple Rule-Based for now, replace with LangGraph later)
    # "If CPA > $50, lower bid. If CPA < $30, raise bid."
    decision = "maintain"
    new_bid_factor = 1.0

    if data.cpa > 50.0:
        decision = "lower_bid"
        new_bid_factor = 0.85
    elif data.cpa < 30.0:
        decision = "raise_bid"
        new_bid_factor = 1.15

    # 4. RELEASE LOCK
    r.delete(lock_key)

    # 5. RETURN COMMAND TO N8N
    return {
        "campaign_id": data.campaign_id,
        "decision": decision,
        "suggested_action": {
            "type": "update_bid",
            "factor": new_bid_factor
        }
    }