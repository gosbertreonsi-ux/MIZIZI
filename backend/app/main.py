# backend/app/main.py — PART 1
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uuid
import os
import sqlite3
import sys
import urllib.request

# --- BULLETPROOF PATH INJECTION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
# backend/app/main.py — PART 2 (DATABASE UPDATED)
app = FastAPI(title="MIZIZI Local API")

# Setup local file asset tracking routes
storage_dir = os.path.join(CURRENT_DIR, "storage")
app.mount("/static", StaticFiles(directory=storage_dir), name="static")

# Define permanent local SQLite file database configurations
DB_PATH = os.path.join(CURRENT_DIR, "mizizi.db")

def init_db():
    """Creates the local database file and the updated jobs table if they don't exist yet."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            prompt TEXT NOT NULL,
            status TEXT NOT NULL,
            aspect_ratio TEXT DEFAULT '16:9',
            resolution TEXT DEFAULT '1024x576',
            steps INTEGER DEFAULT 20,
            seed INTEGER DEFAULT -1,
            engine_mode TEXT DEFAULT 'MOCK',
            video_path TEXT,
            error_message TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


# backend/app/main.py — PART 3 (SCHEMA MAPPING UPDATED)
from mock_engine import generate_video_mock
from comfy_adapter import generate_video_via_comfy

class GenerationRequest(BaseModel):
    prompt: str
    aspect_ratio: str = "16:9"
    resolution: str = "1024x576"
    steps: int = 20
    seed: int = -1
    engine_mode: str = "MOCK"

def is_comfyui_online(address="http://127.0.0.1:8188"):
    """Quickly pings your local ComfyUI app port to see if it's awake."""
    try:
        with urllib.request.urlopen(address, timeout=1.0) as response:
            return response.status == 200
    except Exception:
        return False



# backend/app/main.py — PART 4
def run_ai_job_in_background(job_id: str, prompt: str, steps: int, seed: int, engine_mode: str):
    """Dynamically routes the generation pipeline based on the selected mode flag and live ping state."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE jobs SET status = 'PROCESSING' WHERE id = ?", (job_id,))
    conn.commit()
    
    # --- AUTOMATIC ROUTING MATRIX ---
    if engine_mode == "LIVE" and is_comfyui_online():
        print(f"[Queue Worker] 🌐 Local ComfyUI detected online! Routing job {job_id} to Live pipeline...")
        result = generate_video_via_comfy(prompt, steps, seed, job_id)
    else:
        if engine_mode == "LIVE":
            print(f"[Queue Worker] ⚠️ ComfyUI is offline or unreachable on port 8188. Falling back safely to Mock Simulation!")
        else:
            print(f"[Queue Worker] 🤖 Routing job {job_id} to Local Mock Engine Simulator Pipeline...")
            
        result = generate_video_mock(prompt, job_id)
    
    # Store result variables permanently back into database rows
    cursor.execute("""
        UPDATE jobs 
        SET status = ?, video_path = ?, error_message = ? 
        WHERE id = ?
    """, (result["status"], result["video_path"], result["error_message"], job_id))
    
    conn.commit()
    conn.close()


# backend/app/main.py — PART 5 & 6 (ROUTES UPDATED)
@app.post("/api/generate")
def create_generation_job(request: GenerationRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs (id, prompt, status, aspect_ratio, resolution, steps, seed, engine_mode, video_path, error_message)
        VALUES (?, ?, 'QUEUED', ?, ?, ?, ?, ?, NULL, NULL)
    """, (job_id, request.prompt, request.aspect_ratio, request.resolution, request.steps, request.seed, request.engine_mode))
    conn.commit()
    conn.close()
    
    background_tasks.add_task(run_ai_job_in_background, job_id, request.prompt, request.steps, request.seed, request.engine_mode)
    return {"message": "Job successfully queued", "job_id": job_id, "status": "QUEUED"}

@app.get("/api/jobs")
def get_all_jobs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, prompt, status, video_path, aspect_ratio, steps, seed, engine_mode, resolution FROM jobs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0], "prompt": r[1], "status": r[2], "video_path": r[3],
            "aspect_ratio": r[4], "steps": r[5], "seed": r[6], "engine_mode": r[7], "resolution": r[8]
        }
        for r in rows
    ]



# backend/app/main.py — PART 7
@app.delete("/api/jobs/{job_id}")
def delete_generation_job(job_id: str):
    """Permanently purges a specific history entry row from the sqlite database configuration."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM jobs WHERE id = ?", (job_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Job not found")
    cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()
    return {"message": "Job successfully deleted", "job_id": job_id}
