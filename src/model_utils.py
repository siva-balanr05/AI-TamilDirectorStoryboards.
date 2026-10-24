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



def build_cinematic_image_prompt(scene: dict, shot_detail: str = None) -> str:
    """
    Synthesize complete scene data (all actions, dialogues, characters,
    weather, time, location, props, and camera shot) into a photorealistic
    SDXL visual prompt using Gemini.
    """
    actions_list = scene.get("action", [])
    actions_text = " ".join(actions_list) if isinstance(actions_list, list) else str(actions_list)
    
    dialogues_list = scene.get("dialogues", [])
    dlg_text = ""
    if isinstance(dialogues_list, list):
        dlg_text = " | ".join(f"{d.get('character', '')}: {d.get('line', '')}" for d in dialogues_list if isinstance(d, dict))
        
    shot_focus = shot_detail if shot_detail else "Master Dramatic Scene Shot, 35mm film lens"
    
    prompt = f"""You are an elite film director and AI storyboard prompt engineer.
Convert this screenplay scene into a single, detailed, photorealistic visual image prompt for Stable Diffusion XL.

SCENE DATA:
- Location: {scene.get('location', '')}
- Time of Day: {scene.get('time', '')}
- Weather & Atmosphere: {scene.get('weather', '')}
- Audio/Lighting Cues: {scene.get('audio', '')}
- Characters: {', '.join(scene.get('characters', []))}
- Props: {', '.join(scene.get('props', []))}
- Scene Summary: {scene.get('summary', '')}
- All Scene Actions: {actions_text}
- Dialogues & Emotional Beats: {dlg_text}
- Target Camera Framing & Shot: {shot_focus}

REQUIREMENTS FOR SDXL PROMPT:
1. Translate all concepts into descriptive visual English.
2. Explicitly specify the exact time of day (day/night/dusk) and weather (e.g. rain pouring through windows, lightning flashes, shadows).
3. Specify environment (interior/exterior, set dressing, props, swinging bulbs, dirt/dust).
4. Visually describe character age, ethnicity (South Indian / Tamil cinema aesthetic), physical appearance, clothing, facial expressions (tears, empathy, anger), postures, and specific actions.
5. Translate spoken dialogue into physical expressions, eye contact, and gestures (NEVER put quotes or script lines).
6. Under 110 words. End with: 'cinematic film still, 35mm photography, dramatic Indian cinema lighting, high contrast, photorealistic, 8k, 16:9 widescreen'.
Return ONLY the prompt string, no markdown, no intro."""

    try:
        synth = generate_text(prompt, max_length=1024)
        if synth and len(synth.strip()) > 20:
            synth = synth.replace('```', '').replace('"', '').strip()
            return synth
    except Exception as e:
        print(f"Error synthesizing image prompt: {e}")
        
    # Fallback prompt construction if LLM call fails
    loc = scene.get('location', 'cinema scene')
    summary = scene.get('summary', '')
    return f"Cinematic Indian film still. {summary}. Location: {loc}. Dramatic lighting, 35mm film photography, 16:9 widescreen, photorealistic, 8k."
