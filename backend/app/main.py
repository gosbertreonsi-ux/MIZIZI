# backend/app/main.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uuid
import os
import sqlite3
import sys

# --- BULLETPROOF PATH INJECTION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# 1. Initialize FastAPI Application Instance
app = FastAPI(title="MIZIZI Local API")

# 2. Setup local file asset tracking routes
storage_dir = os.path.join(CURRENT_DIR, "storage")
app.mount("/static", StaticFiles(directory=storage_dir), name="static")

# 3. Define permanent local SQLite file database configurations
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
            steps INTEGER DEFAULT 20,
            seed INTEGER DEFAULT -1,
            engine_mode TEXT DEFAULT 'MOCK',
            video_path TEXT,
            error_message TEXT
        )
    """)
    conn.commit()
    conn.close()

# Kickstart initialization schema structures instantly on spin-up
init_db()

# 4. Import both execution engines
from mock_engine import generate_video_mock
from comfy_adapter import generate_video_via_comfy

# 5. Define clean single structural data schema objects
class GenerationRequest(BaseModel):
    prompt: str
    aspect_ratio: str = "16:9"
    steps: int = 20
    seed: int = -1
    engine_mode: str = "MOCK" # Accept 'MOCK' or 'LIVE' from the frontend toggle

# 6. Asynchronous Background Core Execution Task
def run_ai_job_in_background(job_id: str, prompt: str, steps: int, seed: int, engine_mode: str):
    """Dynamically routes the generation pipeline based on the selected mode flag."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE jobs SET status = 'PROCESSING' WHERE id = ?", (job_id,))
    conn.commit()
    
    # --- DYNAMIC ROUTING MATRIX ---
    if engine_mode == "LIVE":
        print(f"[Queue Worker] 🌐 Routing job {job_id} to Real Live ComfyUI Adapter Pipeline...")
        result = generate_video_via_comfy(prompt, steps, seed, job_id)
    else:
        print(f"[Queue Worker] 🤖 Routing job {job_id} to Local Mock Engine Simulator Pipeline...")
        result = generate_video_mock(prompt, job_id)
    
    # Store result variables permanently back into local memory row models
    cursor.execute("""
        UPDATE jobs 
        SET status = ?, video_path = ?, error_message = ? 
        WHERE id = ?
    """, (result["status"], result["video_path"], result["error_message"], job_id))
    
    conn.commit()
    conn.close()


# --- API ROUTE ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)
def read_root():
    """Serves the front-end web dashboard UI page cleanly."""
    template_path = os.path.join(CURRENT_DIR, "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/generate")
def create_generation_job(request: GenerationRequest, background_tasks: BackgroundTasks):
    """Saves a new job with parameters to the local SQLite database and triggers the background task."""
    job_id = str(uuid.uuid4())
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs (id, prompt, status, aspect_ratio, steps, seed, engine_mode, video_path, error_message)
        VALUES (?, ?, 'QUEUED', ?, ?, ?, ?, NULL, NULL)
    """, (job_id, request.prompt, request.aspect_ratio, request.steps, request.seed, request.engine_mode))
    conn.commit()
    conn.close()
    
    # Fire the async pipeline worker process off to background tasks threads with dynamic engine tracking
    background_tasks.add_task(run_ai_job_in_background, job_id, request.prompt, request.steps, request.seed, request.engine_mode)
    return {"message": "Job successfully queued", "job_id": job_id, "status": "QUEUED"}

@app.get("/api/jobs")
def get_all_jobs():
    """Fetches every single generation job saved in the history database matrix with configuration info."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, prompt, status, video_path, aspect_ratio, steps, seed, engine_mode FROM jobs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0], "prompt": r[1], "status": r[2], "video_path": r[3],
            "aspect_ratio": r[4], "steps": r[5], "seed": r[6], "engine_mode": r[7]
        }
        for r in rows
    ]

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    """Reads a singular highly targeted generation job state row straight from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, prompt, status, video_path, error_message, aspect_ratio, steps, seed, engine_mode FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {
        "id": row[0], "prompt": row[1], "status": row[2], "video_path": row[3], "error_message": row[4],
        "aspect_ratio": row[5], "steps": row[6], "seed": row[7], "engine_mode": row[8]
    }

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
