import os
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Configure Gemini
_gemini_key = os.getenv("GEMINI_API_KEY")
if _gemini_key:
    genai.configure(api_key=_gemini_key)

# Fallback chain: each model has its own separate daily quota
_GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-flash-latest",
]


def generate_text(prompt: str, max_length: int = 8192) -> str:
    last_error = None
    for model_name in _GEMINI_MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_length,
                    temperature=0.7,
                )
            )
            return response.text
        except Exception as e:
            # 429 quota exhausted — try next model
            if "429" in str(e) or "quota" in str(e).lower():
                print(f"Quota exhausted for {model_name}, trying next model...")
                last_error = e
                continue
            raise e
    raise last_error


def generate_image(prompt: str, output_path: str) -> bool:
    api_key = os.getenv("STABILITY_API_KEY")
    if not api_key:
        print("STABILITY_API_KEY not set")
        return False

    try:
        response = requests.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "text_prompts": [{"text": prompt, "weight": 1}],
                "cfg_scale": 7,
                # SDXL v1 endpoint accepts only specific width/height pairs.
                "height": 768,
                "width": 1344,
                "samples": 1,
                "steps": 30,
            },
            timeout=60,
        )
        try:
            response.raise_for_status()
        except Exception as http_err:
            # Log error details to file
            with open("stability_image_error.log", "a", encoding="utf-8") as logf:
                logf.write(f"HTTP error: {http_err}\nStatus: {response.status_code}\nResponse: {response.text}\nPrompt: {prompt}\n\n")
            print(f"HTTP error: {http_err}, see stability_image_error.log for details.")
            return False
        data = response.json()
        if "artifacts" not in data or not data["artifacts"] or "base64" not in data["artifacts"][0]:
            # Log unexpected response
            with open("stability_image_error.log", "a", encoding="utf-8") as logf:
                logf.write(f"No image in response. Status: {response.status_code}\nResponse: {response.text}\nPrompt: {prompt}\n\n")
            print("No image data in Stability API response, see stability_image_error.log for details.")
            return False
        img_data = base64.b64decode(data["artifacts"][0]["base64"])
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(img_data)
        return True
    except Exception as e:
        # Log any other error
        with open("stability_image_error.log", "a", encoding="utf-8") as logf:
            logf.write(f"General error: {str(e)}\nPrompt: {prompt}\n\n")
        print(f"Error generating image: {str(e)}, see stability_image_error.log for details.")
        return False