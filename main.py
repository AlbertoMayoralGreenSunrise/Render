# main.py 
from fastapi import FastAPI, HTTPException 
from pydantic import BaseModel 
from wattwin import process_wattwin_order
import subprocess
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


from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.post("/wattwin-webhook")
async def wattwin_webhook(payload: dict):
    try:
        # Extraer información directamente del payload
        order_id = payload.get("id")
        if not order_id:
            raise HTTPException(status_code=400, detail="No order id provided in payload")

        order_name = payload.get("name", "")
        stage_name = payload.get("stage", {}).get("name", "")
        stage_updated_at = payload.get("stage", {}).get("updatedAt", "")

        # Llamar a tu función pasando la información relevante
        logs = process_wattwin_order(
            order_id=order_id,
            order_name=order_name,
            stage_name=stage_name,
            stage_date=stage_updated_at
        )

        return {"status": "success", "logs": logs}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

