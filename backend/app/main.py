# backend/app/main.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uuid
import os

# 1. ALWAYS CREATE THE APP OBJECT FIRST
app = FastAPI(title="MIZIZI Local API")

# Import the mock engine we built together
from backend.app.mock_engine import generate_video_mock

# A simple dictionary to store jobs in memory for now
jobs_database = {}

# Set up local asset folders
storage_dir = os.path.join(os.path.dirname(__file__), "storage")
app.mount("/static", StaticFiles(directory=storage_dir), name="static")

# Define what data we expect from the frontend
class GenerationRequest(BaseModel):
    prompt: str

# --- BACKGROUND TASK WORKER ---
def run_ai_job_in_background(job_id: str, prompt: str):
    """Updates the database state as the mock engine processes the request."""
    jobs_database[job_id]["status"] = "PROCESSING"
    
    # Run our mock engine simulation
    result = generate_video_mock(prompt, job_id)
    
    # Update the job database with the final results
    jobs_database[job_id]["status"] = result["status"]
    jobs_database[job_id]["video_path"] = result["video_path"]
    jobs_database[job_id]["error_message"] = result["error_message"]


# --- CODE ENDPOINTS (ORDERED CORRECTLY) ---

@app.get("/", response_class=HTMLResponse)
def read_root():
    """Serves the front-end web dashboard page."""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/generate")
def create_generation_job(request: GenerationRequest, background_tasks: BackgroundTasks):
    """Accepts a prompt, creates a Job ID, and queues it instantly."""
    job_id = str(uuid.uuid4())
    
    jobs_database[job_id] = {
        "id": job_id,
        "prompt": request.prompt,
        "status": "QUEUED",
        "video_path": None,
        "error_message": None
    }
    
    background_tasks.add_task(run_ai_job_in_background, job_id, request.prompt)
    return {"message": "Job successfully queued", "job_id": job_id, "status": "QUEUED"}

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    """Allows the frontend to check up on a job's progress by its ID."""
    job = jobs_database.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
