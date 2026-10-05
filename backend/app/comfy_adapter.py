# backend/app/comfy_adapter.py — PART 1 (UPDATED SYSTEM PATH)
import json
import urllib.request
import urllib.parse
import os
import shutil
import glob
import time

COMFYUI_ADDRESS = "127.0.0.1:8188"

# Mapped explicitly to your local folder configuration path matrix
COMFYUI_OUTPUT_DIR = os.path.abspath("C:/Comfy Desktop/output")


# backend/app/comfy_adapter.py — PART 2
def generate_video_via_comfy(prompt: str, steps: int, seed: int, job_id: str) -> dict:
    """Connects to your local running ComfyUI desktop instance and processes real visual pixels."""
    print(f"\n[ComfyUI Adapter] 🌐 Sending prompt parameters to local port: {COMFYUI_ADDRESS}...")
    
    # This JSON schema matches the structural execution block ComfyUI expects over its API port listener
    comfy_workflow = {
        "3": {
            "inputs": {"text": prompt, "clip": ["4", 0]},
            "class_type": "CLIPTextEncode"
        },
        "4": {"class_type": "CLIPLoader", "inputs": {"clip_name": "t5xxl_fp16.safetensors"}},
        "6": {
            "inputs": {"seed": seed, "steps": steps, "cfg": 6.0, "sampler_name": "euler", "scheduler": "normal", "latent_image": ["7", 0]},
            "class_type": "KSampler"
        },
        "7": {"class_type": "EmptyVideoLatentImage", "inputs": {"width": 512, "height": 512, "length": 16}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["9", 0]}},
        "9": {"class_type": "VAELoader", "inputs": {"vae_name": "video_vae.safetensors"}},
        "10": {"class_type": "VHS_VideoCombine", "inputs": {"images": ["8", 0], "filename_prefix": f"mizizi_{job_id}", "format": "video/h264-mp4"}}
    }
    
    payload = {"prompt": comfy_workflow}
    data = json.dumps(payload).encode('utf-8')
    
    try:
        url = f"http://{COMFYUI_ADDRESS}/prompt"
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req) as response:
            reply = json.loads(response.read().decode('utf-8'))
            prompt_id = reply.get("prompt_id")
            print(f"[ComfyUI Adapter] 🚀 Handshake success! Node graph running. Prompt ID: {prompt_id}")
        
        # Define destination paths inside MIZIZI's static public delivery folder
        dest_dir = os.path.join(os.path.dirname(__file__), "storage", "generations")
        os.makedirs(dest_dir, exist_ok=True)
        target_filename = f"{job_id}.mp4"
        final_dest_path = os.path.join(dest_dir, target_filename)
        
        print("[ComfyUI Adapter] ⏳ Polling your ComfyUI output folder for the rendered file...")
        
        # Loop and check the folder every 3 seconds for the finished asset file handle
        max_attempts = 200
        for attempt in range(max_attempts):
            time.sleep(3)
            
            search_pattern = os.path.join(COMFYUI_OUTPUT_DIR, f"mizizi_{job_id}*.mp4")
            found_files = glob.glob(search_pattern)
            
            if found_files:
                real_generated_file = found_files[0]
                print(f"[ComfyUI Adapter] 🎉 Real video file detected at: {real_generated_file}")
                
                # Clone the real media file out of ComfyUI and save it straight into MIZIZI
                shutil.copy(real_generated_file, final_dest_path)
                print(f"[ComfyUI Adapter] ☑️ Real file successfully synchronized to MIZIZI dashboard.")
                
                return {
                    "status": "COMPLETED",
                    "video_path": f"/static/generations/{target_filename}",
                    "error_message": None
                }
                
        raise TimeoutError("The processing loop timed out before your hardware finished rendering.")
            
    except Exception as e:
        print(f"[ComfyUI Adapter] ❌ Execution pipeline error layout: {str(e)}")
        return {
            "status": "FAILED",
            "video_path": None,
            "error_message": f"Real pipeline processing failed: {str(e)}"
        }
