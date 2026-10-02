# backend/app/main.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uuid
import os

# Import the mock engine we built together last time
from backend.app.mock_engine import generate_video_mock


app = FastAPI(title="MIZIZI Local API")

# A simple dictionary to store jobs in memory for now (instead of a complex database)
# In real production, this becomes PostgreSQL
jobs_database = {}

# Make our generated files accessible to the browser via a URL (e.g., http://localhost:8000/static/generations/abc.mp4)
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

# --- API ENDPOINTS ---

@app.post("/api/generate")
def create_generation_job(request: GenerationRequest, background_tasks: BackgroundTasks):
    """1. Accepts a prompt, creates a Job ID, and queues it instantly."""
    job_id = str(uuid.uuid4())
    
    # Initialize the job in our local memory database
    jobs_database[job_id] = {
        "id": job_id,
        "prompt": request.prompt,
        "status": "QUEUED",
        "video_path": None,
        "error_message": None
    }
    
    # Tell FastAPI to run this heavy task in the background without blocking the response
    background_tasks.add_task(run_ai_job_in_background, job_id, request.prompt)
    
    # Reply instantly to the user
    return {"message": "Job successfully queued", "job_id": job_id, "status": "QUEUED"}

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    """2. Allows the frontend to check up on a job's progress by its ID."""
    job = jobs_database.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
