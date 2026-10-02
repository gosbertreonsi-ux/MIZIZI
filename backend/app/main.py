# backend/app/main.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uuid
import os
import sqlite3

app = FastAPI(title="MIZIZI Local API")

# Import our mock engine
from backend.app.mock_engine import generate_video_mock

# Setup storage directory
storage_dir = os.path.join(os.path.dirname(__file__), "storage")
app.mount("/static", StaticFiles(directory=storage_dir), name="static")

# Define the file location for our local database
DB_PATH = os.path.join(os.path.dirname(__file__), "mizizi.db")

@app.get("/api/jobs")
def get_all_jobs():
    """Fetches every generation job saved in the history database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, prompt, status, video_path FROM jobs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    # Map raw rows into clean dictionaries for the frontend
    return [
        {"id": r[0], "prompt": r[1], "status": r[2], "video_path": r[3]}
        for r in rows
    ]


def init_db():
    """Creates the local database file and the jobs table if they don't exist yet."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            prompt TEXT NOT NULL,
            status TEXT NOT NULL,
            video_path TEXT,
            error_message TEXT
        )
    """)
    conn.commit()
    conn.close()

# Initialize the database immediately when the server starts
init_db()

class GenerationRequest(BaseModel):
    prompt: str

# --- BACKGROUND TASK WORKER ---
def run_ai_job_in_background(job_id: str, prompt: str):
    """Updates the real database file as processing steps change."""
    # 1. Update status to PROCESSING
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE jobs SET status = 'PROCESSING' WHERE id = ?", (job_id,))
    conn.commit()
    
    # 2. Trigger our simulated AI processing engine
    result = generate_video_mock(prompt, job_id)
    
    # 3. Update the database file with final results (Completed or Failed)
    cursor.execute("""
        UPDATE jobs 
        SET status = ?, video_path = ?, error_message = ? 
        WHERE id = ?
    """, (result["status"], result["video_path"], result["error_message"], job_id))
    
    conn.commit()
    conn.close()

# --- API ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)
def read_root():
    """Serves the front-end web dashboard page."""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/generate")
def create_generation_job(request: GenerationRequest, background_tasks: BackgroundTasks):
    """Saves a new job to the local SQLite database file and triggers the background task."""
    job_id = str(uuid.uuid4())
    
    # Insert new job into SQLite file
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs (id, prompt, status, video_path, error_message)
        VALUES (?, ?, 'QUEUED', NULL, NULL)
    """, (job_id, request.prompt))
    conn.commit()
    conn.close()
    
    # Send off to background processing without waiting
    background_tasks.add_task(run_ai_job_in_background, job_id, request.prompt)
    return {"message": "Job successfully queued", "job_id": job_id, "status": "QUEUED"}

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    """Reads the job state straight from the SQLite database file."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, prompt, status, video_path, error_message FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {
        "id": row[0],
        "prompt": row[1],
        "status": row[2],
        "video_path": row[3],
        "error_message": row[4]
    }
