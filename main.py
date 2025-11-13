from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests

app = FastAPI()

WATTWIN_API_KEY = os.getenv("WATTWIN_API_KEY")
WATTWIN_BASE = "https://public.api.wattwin.com/v1"
RINGOVER_API_KEY = os.getenv("RINGOVER_API_KEY")
RINGOVER_BASE = "https://public-api.ringover.com/v2"

class RingoverData(BaseModel):
    call_id: str
    channel_id: str
    summary: str
    ringover_call_path: str

class RingoverPayload(BaseModel):
    resource: str
    event: str
    timestamp: int
    data: RingoverData
    attempt: int

from ringover import process_ringover_call  # importar la lógica desde ringover.py

@app.get("/")
def root():
    return {"message": "Este endpoint solo acepta POST desde Ringover"}

@app.post("/ringover-webhook")
async def ringover_webhook(payload: RingoverPayload):
    try:
        return process_ringover_call(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
