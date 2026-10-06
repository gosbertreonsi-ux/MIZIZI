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


# backend/app/comfy_adapter.py — PART 2 (STABILIZED CORE HANDSHAKE WORKING)
def generate_video_via_comfy(prompt: str, steps: int, seed: int, job_id: str, resolution_str: str = "1024x576") -> dict:
    """Connects to local ComfyUI using standard core nodes with fully connected mapping wires."""
    print(f"\n[ComfyUI Adapter] 🌐 Processing layout attributes matrix for job {job_id}...")
    
    # 1. Parse your dashboard dropdown selection into separate Width & Height integers
    try:
        width_part, height_part = resolution_str.split('x')
        target_width = int(width_part)
        target_height = int(height_part)
        print(f"[ComfyUI Adapter] 📐 Custom Resolution Map Extracted -> Width: {target_width}px | Height: {target_height}px")
    except Exception:
        target_width = 512
        target_height = 512
        print("[ComfyUI Adapter] ⚠️ Using default 512x512 fallback sizing configuration.")

    # 2. Correctly connected default core graph payload structure (No empty/missing wires)
    comfy_workflow = {
        "1": {
            "inputs": {
                "ckpt_name": "v1-5-pruned-emaonly.safetensors" # Standard default free open-source baseline model name
            },
            "class_type": "CheckpointLoaderSimple"
        },
        "2": {
            "inputs": {
                "text": prompt,
                "clip": ["1", 1] # Connects the CLIP wire from our Checkpoint Loader (Node 1, slot 1)
            },
            "class_type": "CLIPTextEncode"
        },
        "3": {
            "inputs": {
                "text": "bad quality, blurry, low resolution, text, watermark", # Standard negative prompt safety matrix
                "clip": ["1", 1] # Connects the CLIP wire from our Checkpoint Loader
            },
            "class_type": "CLIPTextEncode"
        },
        "4": {
            "inputs": {
                "width": target_width,
                "height": target_height,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage"
        },
        "5": {
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["1", 0],       # Wires up the Model stream from Node 1 (slot 0)
                "positive": ["2", 0],    # Wires up the Positive Prompt stream from Node 2
                "negative": ["3", 0],    # Wires up the Negative Prompt stream from Node 3
                "latent_image": ["4", 0] # Wires up the Latent Layout grid from Node 4
            },
            "class_type": "KSampler"
        },
        "6": {
            "inputs": {
                "samples": ["5", 0], # Wires up the generated latent math from our KSampler
                "vae": ["1", 2]      # Wires up the VAE decoder direct from the Checkpoint Loader (Node 1, slot 2)
            },
            "class_type": "VAEDecode"
        },
        "7": {
            "inputs": {
                "images": ["6", 0],
                "filename_prefix": f"mizizi_{job_id}"
            },
            "class_type": "SaveImage"
        }
    }
    
    payload = {"prompt": comfy_workflow}
    data = json.dumps(payload).encode('utf-8')
    
    try:
        url = f"http://{COMFYUI_ADDRESS}/prompt"
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req) as response:
            reply = json.loads(response.read().decode('utf-8'))
            print(f"[ComfyUI Adapter] 🚀 Handshake success! Core graph accepted. Prompt ID: {reply.get('prompt_id')}")
        
        dest_dir = os.path.join(os.path.dirname(__file__), "storage", "generations")
        os.makedirs(dest_dir, exist_ok=True)
        
        target_filename = f"{job_id}.png"
        final_dest_path = os.path.join(dest_dir, target_filename)
        
        print("[ComfyUI Adapter] ⏳ Polling local directory for real generated output asset...")
        
        max_attempts = 200
        for attempt in range(max_attempts):
            time.sleep(3)
            search_pattern = os.path.join(COMFYUI_OUTPUT_DIR, f"mizizi_{job_id}*.png")
            found_files = glob.glob(search_pattern)
            
            if found_files:
                real_file = found_files
                shutil.copy(real_file, final_dest_path)
                print("[ComfyUI Adapter] ☑️ Real generation asset cloned safely into MIZIZI UI structures.")
                return {"status": "COMPLETED", "video_path": f"/static/generations/{target_filename}", "error_message": None}
                
        raise TimeoutError("Local processing pipeline took too long to compile asset to drive handles.")
            
    except Exception as e:
        print(f"[ComfyUI Adapter] ❌ Pipeline Exception: {str(e)}")
        return {"status": "FAILED", "video_path": None, "error_message": f"Live generation thread failed: {str(e)}"}
