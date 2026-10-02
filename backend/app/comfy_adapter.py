# backend/app/comfy_adapter.py — PART 1 (REAL SYSTEM PATHING)
import json
import urllib.request
import urllib.parse
import os
import shutil
import glob
import time

COMFYUI_ADDRESS = "127.0.0.1:8188"

# CHANGE THIS to your actual ComfyUI output path so MIZIZI can find the real videos!
COMFYUI_OUTPUT_DIR = os.path.abspath("C:/ComfyUI_windows_portable/ComfyUI/output")


# backend/app/comfy_adapter.py — PART 2 (REAL GENERATION & EXTRACTION LOOP)
def generate_video_via_comfy(prompt: str, steps: int, seed: int, job_id: str) -> dict:
    """Connects to live ComfyUI, runs a real generation workflow, and copies the output video."""
    print(f"\n[ComfyUI] 🌐 Sending prompt matrix to local server port at {COMFYUI_ADDRESS}...")
    
    # This structure mirrors a real production text-to-video API node loop setup
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
            print(f"[ComfyUI] 🚀 Handshake success! Node graph running in background. Prompt ID: {prompt_id}")
        
        # --- NEW REAL-TIME POLLING LOOP ---
        # Watch the ComfyUI output directory until the real video file appears
        dest_dir = os.path.join(os.path.dirname(__file__), "storage", "generations")
        os.makedirs(dest_dir, exist_ok=True)
        target_filename = f"{job_id}.mp4"
        final_dest_path = os.path.join(dest_dir, target_filename)
        
        print("[ComfyUI] ⏳ Local hardware is rendering frames. Polling output directory...")
        
        max_attempts = 120  # Max waiting time (e.g., 2 minutes)
        for attempt in range(max_attempts):
            time.sleep(2)  # Check every 2 seconds
            
            # Look for the unique file prefix we assigned in Node 10
            search_pattern = os.path.join(COMFYUI_OUTPUT_DIR, f"mizizi_{job_id}*.mp4")
            found_files = glob.glob(search_pattern)
            
            if found_files:
                real_video_file = found_files[0]
                print(f"[ComfyUI] 🎉 Real video file detected at: {real_video_file}")
                
                # Copy the file safely out of ComfyUI and drop it directly into MIZIZI's UI gallery static folder
                shutil.copy(real_video_file, final_dest_path)
                print(f"[ComfyUI] ☑️ Asset successfully synchronized to MIZIZI gallery.")
                
                return {
                    "status": "COMPLETED",
                    "video_path": f"/static/generations/{target_filename}",
                    "error_message": None
                }
                
        raise TimeoutError("ComfyUI generation took too long or failed to write file to disk.")
            
    except Exception as e:
        print(f"[ComfyUI] ❌ Real pipeline generation error instance: {str(e)}")
        return {
            "status": "FAILED",
            "video_path": None,
            "error_message": f"Pipeline processing failed: {str(e)}"
        }
