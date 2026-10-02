# backend/app/comfy_adapter.py
import json
import urllib.request
import urllib.parse
import os

COMFYUI_ADDRESS = "127.0.0.1:8188"

def generate_video_via_comfy(prompt: str, steps: int, seed: int, job_id: str) -> dict:
    """
    Connects to a local running ComfyUI instance, injects user configuration values, 
    and handles the generation request over HTTP API.
    """
    print(f"\n[ComfyUI Adapter] Connecting to live ComfyUI instance at {COMFYUI_ADDRESS}...")
    
    # 1. Define a minimal ComfyUI workflow JSON mapping.
    # In a full setup, this matches your exact model workflow node keys (e.g., KSampler, Load Model).
    # For now, we outline the structural node template payload ComfyUI expects.
    comfy_workflow = {
        "1": {
            "inputs": {
                "text": prompt
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Prompt)"}
        },
        "2": {
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": 6.0,
                "sampler_name": "euler",
                "scheduler": "normal"
            },
            "class_type": "KSampler",
            "_meta": {"title": "KSampler Node"}
        }
    }

    # Wrap it inside the root prompt payload structure required by ComfyUI's API listener
    payload = {"prompt": comfy_workflow}
    data = json.dumps(payload).encode('utf-8')
    
    try:
        # 2. Fire an HTTP POST request straight to ComfyUI's local API receiver port
        url = f"http://{COMFYUI_ADDRESS}/prompt"
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        print(f"[ComfyUI Adapter] Submitting payload workflow to /prompt endpoint...")
        with urllib.request.urlopen(req) as response:
            reply = json.loads(response.read().decode('utf-8'))
            comfy_prompt_id = reply.get("prompt_id")
            print(f"[ComfyUI Adapter] Success! ComfyUI accepted job. Prompt ID: {comfy_prompt_id}")
            
            # For development safety, if ComfyUI generates files inside its own internal view folder,
            # we point our database tracking to it or return a confirmation block.
            return {
                "status": "COMPLETED",
                "video_path": "/static/generations/placeholder_output.mp4", # Will be updated with ComfyUI's physical filename later
                "error_message": None
            }
            
    except Exception as e:
        print(f"[ComfyUI Adapter] ❌ Connection failed: Is ComfyUI turned off or running on a different port?")
        return {
            "status": "FAILED",
            "video_path": None,
            "error_message": f"Could not establish handshake with local ComfyUI pipeline: {str(e)}"
        }
