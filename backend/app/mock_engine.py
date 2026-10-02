# backend/app/mock_engine.py
import os
import time
import random

def generate_video_mock(prompt: str, job_id: str) -> dict:
    """
    Simulates generating a video from a prompt without requiring a GPU.
    Returns a dictionary indicating the result status and the local file path.
    """
    print(f"\n[AI Engine] 🚀 Received job {job_id} with prompt: '{prompt}'")
    
    # 1. Simulate the "QUEUED" state hanging for a moment
    time.sleep(1)
    print(f"[AI Engine] ⏳ Job {job_id} moved to PROCESSING...")

    # 2. Simulate incremental rendering steps
    total_steps = 5
    for step in range(1, total_steps + 1):
        time.sleep(0.5)  # Pause to simulate generation effort
        percent = int((step / total_steps) * 100)
        print(f"[AI Engine] ⚙️ Job {job_id}: Processing workflow nodes... {percent}%")

    # 3. Code-level error testing injection
    # If your prompt contains the word "fail", this simulates a system crash or VRAM error
    if "fail" in prompt.lower():
        print(f"[AI Engine] ❌ Critical Error: Simulated system crash for testing.")
        return {
            "status": "FAILED", 
            "error_message": "VRAM allocation failed inside KSampler node simulation."
        }

    # 4. Create an actual empty file on your hard drive to prove storage tracking works
    storage_dir = os.path.join(os.path.dirname(__file__), "storage", "generations")
    os.makedirs(storage_dir, exist_ok=True)
    
    file_name = f"{job_id}.mp4"
    file_path = os.path.join(storage_dir, file_name)
    
    # Write a fake minimal MP4 header byte signature
    with open(file_path, "wb") as mock_file:
        mock_file.write(b"\x00\x00\x00\x18ftypmp42")

    print(f"[AI Engine] 🎉 Generation Complete! File saved to: backend/app/storage/generations/{file_name}")
    
    return {
        "status": "COMPLETED",
        "video_path": f"/static/generations/{file_name}",
        "error_message": None
    }

# Quick local test to verify it works out-of-the-box
if __name__ == "__main__":
    print("--- Running Test 1: Successful Video Generation ---")
    success_result = generate_video_mock("A futuristic digital marketplace", "job_001")
    print(success_result)
    
    print("\n--- Running Test 2: Error Handler Simulation ---")
    fail_result = generate_video_mock("Make this generation fail for testing", "job_002")
    print(fail_result)
