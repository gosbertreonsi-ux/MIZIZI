# backend/app/comfy_adapter.py — PART 1 (PORTABLE RESOLUTION ADJUSTMENT)
import json
import urllib.request
import urllib.parse
import os
import shutil
import glob
import time

# Connected to your active portable port engine listener
COMFYUI_ADDRESS = "127.0.0.1:8188"

# Updated to target the correct folder structure of your portable installation path
COMFYUI_OUTPUT_DIR = os.path.abspath("C:/ComfyUI_windows_portable/ComfyUI/output")

# backend/app/comfy_adapter.py — PART 2 (NODE PARAMETERS EXTRACTION)
def generate_video_via_comfy(prompt: str, steps: int, seed: int, job_id: str, resolution_str: str = "1024x576") -> dict:
    """Parses custom layout dimension arguments and submits them natively to ComfyUI nodes."""
    print(f"\n[ComfyUI Adapter] 🌐 Processing layout attributes matrix for job {job_id}...")
    
    # SPLITTING LOGIC: Breaks "1024x576" into individual numeric width/height integers
    try:
        width_part, height_part = resolution_str.split('x')
        target_width = int(width_part)
        target_height = int(height_part)
        print(f"[ComfyUI Adapter] 📐 Custom Resolution Map Extracted -> Width: {target_width}px | Height: {target_height}px")
    except Exception:
        # Secure safety fallback if string reading hiccups
        target_width = 1024
        target_height = 576
        print("[ComfyUI Adapter] ⚠️ Failed parsing width matrix string. Using default 1024x576 HD fallback framework.")

    # Injected variables straight into Node 7 (EmptyVideoLatentImage) 
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
        "7": {
            "inputs": {"width": target_width, "height": target_height, "length": 16},
            "class_type": "EmptyVideoLatentImage"
        },
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
            print(f"[ComfyUI Adapter] 🚀 Handshake success! Live node job submitted. ID: {reply.get('prompt_id')}")
        
        # System storage delivery paths setup
        dest_dir = os.path.join(os.path.dirname(__file__), "storage", "generations")
        os.makedirs(dest_dir, exist_ok=True)
        target_filename = f"{job_id}.mp4"
        final_dest_path = os.path.join(dest_dir, target_filename)
        
        print("[ComfyUI Adapter] ⏳ Polling target directory for generation asset compile handle...")
        
        max_attempts = 200
        for attempt in range(max_attempts):
            time.sleep(3)
            search_pattern = os.path.join(COMFYUI_OUTPUT_DIR, f"mizizi_{job_id}*.mp4")
            found_files = glob.glob(search_pattern)
            
            if found_files:
                real_file = found_files[0]
                shutil.copy(real_file, final_dest_path)
                print("[ComfyUI Adapter] ☑️ Real generation asset cloned safely into MIZIZI UI structures.")
                return {"status": "COMPLETED", "video_path": f"/static/generations/{target_filename}", "error_message": None}
                
        raise TimeoutError("Local processing pipeline took too long to compile asset to drive handles.")
            
    except Exception as e:
        print(f"[ComfyUI Adapter] ❌ Pipeline Exception: {str(e)}")
        return {"status": "FAILED", "video_path": None, "error_message": f"Live generation thread failed: {str(e)}"}
