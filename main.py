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

@app.post("/wattwin-webhook")
async def wattwin_webhook(payload: dict):
    try:
        instance_id = payload.get("id")
        if not instance_id:
            raise HTTPException(status_code=400, detail="No id provided in payload")

        nombre = payload.get("name", "")
        fecha = payload.get("stage", {}).get("updatedAt", "")
        stage_id = payload.get("stageId")  # stageId directo desde payload

        # Stage permitido
        STAGE_ALLOWED = "684ad5a0d313a30d7ba4036e"

        if stage_id != STAGE_ALLOWED:
            return {
                "status": "skipped",
                "message": f"StageId {stage_id} no coincide, webhook ignorado"
            }

        logs = process_wattwin_order(instance_id, nombre, fecha, stage_id)

        return {"status": "success", "logs": logs}

    except Exception as e:
        print(f"[ERROR] /wattwin-webhook failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


