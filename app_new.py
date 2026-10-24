"""
AI Director - Multi-language Script Analysis and Storyboard Generation
"""
import os
import json
import re
import shutil
from pathlib import Path
import time
import random
from functools import wraps
import streamlit as st
from streamlit import rerun
import base64
import docx2txt
from PyPDF2 import PdfReader
from src.model_utils import generate_text, generate_image, build_cinematic_image_prompt
from src.language_utils import LanguageManager

def clear_workspace_data(startup=False):
    """Clear all generated files and reset the workspace"""
    try:
        shutil.rmtree('storyboards', ignore_errors=True)
        os.makedirs('storyboards/scene_01', exist_ok=True)
        
        if os.path.exists('script_breakdown.json'):
            os.remove('script_breakdown.json')
            
        if not startup:
            keys_to_clear = [k for k in st.session_state.keys() 
                           if k not in ['initialized', 'selected_language']]
            for key in keys_to_clear:
                del st.session_state[key]
        return True
    except Exception as e:
        if not startup:
            st.error(f"Error clearing workspace: {str(e)}")
        return False

def startup_cleanup():
    """Clean up old files on app startup"""
    if 'initialized' not in st.session_state:
        clear_workspace_data(startup=True)
        st.session_state.initialized = True
    if 'selected_language' not in st.session_state:
        st.session_state.selected_language = 'tamil'
    if 'script_text' not in st.session_state:
        st.session_state.script_text = ''

def retry_with_backoff(retries=3, backoff_in_seconds=1):
    """Retry decorator with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        raise e
                    sleep = (backoff_in_seconds * 2 ** x + random.uniform(0, 1))
                    time.sleep(sleep)
                    x += 1
        return wrapper
    return decorator

@retry_with_backoff(retries=3, backoff_in_seconds=2)
def safe_generate_content(prompt: str) -> str:
    """Safely generate content with retries"""
    try:
        return generate_text(prompt)
    except Exception as e:
        st.error(f"Model call error: {e}")
        raise e

def extract_json_from_text(text: str) -> dict:
    """Extract JSON object from text"""
    if not text:
        return None
    
    # Try direct JSON parsing first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Find JSON-like structure in text
        start = text.find("{")
        if start == -1:
            return None
            
        count = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                count += 1
            elif text[i] == "}":
                count -= 1
                if count == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        continue
        return None

def analyze_dialogue(dialogue: str) -> dict:
    """Analyze the emotional content of a dialogue"""
    emotion_prompt = LanguageManager.get_emotion_prompt(st.session_state.selected_language)
    prompt = (
        f"{emotion_prompt}\n\n"
        f"Dialogue: {dialogue}\n\n"
        "Respond in JSON format:\n"
        "{\n"
        '    "emotion": "happiness/anger/sadness/fear/surprise",\n'
        '    "intensity": "1 to 10",\n'
        '    "tone": "normal/intense/humorous/frustrated"\n'
        "}"
    )
    try:
        response = generate_text(prompt)
        return extract_json_from_text(response) or {
            "emotion": "neutral",
            "intensity": 5,
            "tone": "normal"
        }
    except Exception as e:
        print(f"⚠️ Dialogue analysis error: {e}")
        return {"emotion": "neutral", "intensity": 5, "tone": "normal"}

def get_camera_angles(emotion: str, intensity: int, tone: str) -> list:
    """Get appropriate camera angles based on emotion and intensity"""
    angle_map = {
        "happiness": ["Medium Shot", "Tracking Shot", "High Angle"],
        "anger": ["Close-up", "Dutch Angle", "Steadicam Shot"],
        "sadness": ["Extreme Close-up", "High Angle", "Slow Tracking Shot"],
        "fear": ["Close-up", "Low Angle", "Handheld Shot"],
        "surprise": ["Close-up", "Snap Zoom", "Over-the-Shoulder"],
        "neutral": ["Medium Shot", "Two Shot", "Master Shot"]
    }
    
    base_angles = angle_map.get(emotion.lower(), ["Medium Shot", "Close-up"])
    
    # Add intensity-based angles
    if intensity >= 8:
        base_angles.extend(["Extreme Close-up", "Dutch Angle"])
    elif intensity <= 3:
        base_angles.extend(["Long Shot", "Wide Shot"])
        
    # Add tone-based angles
    if tone == "intense":
        base_angles.extend(["Handheld Shot", "Low Angle"])
    elif tone == "humorous":
        base_angles.extend(["Wide Shot", "High Angle"])
        
    return list(set(base_angles))  # Remove duplicates

def translate_to_english(text: str) -> str:
    """Translate text to English for image generation"""
    if not text or not text.strip():
        return ""
    if st.session_state.selected_language == 'english':
        return text
    
    prompt = (
        f"Translate this {st.session_state.selected_language} text into "
        f"cinematic English suitable for AI image generation. "
        f"Reply with English text only:\n\n{text}"
    )
    result = safe_generate_content(prompt).strip()
    if not result:
        st.warning(f"Translation failed for: {text[:50]}...")
        return text.strip()
    return result

def suggest_cinematic_shots(scene_data: dict) -> list:
    """Generate cinematographer-style shot suggestions"""
    shot_prompt = LanguageManager.get_shot_prompt(st.session_state.selected_language)
    prompt = (
        f"{shot_prompt}\n\n"
        f"Scene Details:\n"
        f"- Location: {scene_data.get('location', '')}\n"
        f"- Characters: {', '.join(scene_data.get('characters', []))}\n"
        f"- Props: {', '.join(scene_data.get('props', []))}\n"
        f"- Summary: {scene_data.get('summary', '')}"
    )
    response = safe_generate_content(prompt)
    shots_data = extract_json_from_text(response)
    return shots_data.get('shots', []) if shots_data else []

def clean_prompt(text: str, max_len: int = 1900) -> str:
    """Clean and truncate prompt text"""
    text = text.replace("```", "").strip()
    text = " ".join(line.strip() for line in text.split("\n") if line.strip())
    if len(text) > max_len:
        text = text[: max_len - 3] + "..."
    return text

def ensure_english(text: str) -> str:
    """Ensure text is in English by translating if needed"""
    if st.session_state.selected_language == 'english':
        return text
    if any(ord(char) > 127 for char in text):
        return translate_to_english(text)
    return text

# ---------------------------
# New / UI Helper functions
# ---------------------------

def encode_image_to_base64(path: Path):
    """Return data URI for an image if file exists, else None"""
    if not path or not path.exists():
        return None
    try:
        with open(path, "rb") as f:
            data = f.read()
            encoded = base64.b64encode(data).decode("utf-8")
            mime = "image/png"
            # try to guess extension
            if path.suffix.lower() in [".jpg", ".jpeg"]:
                mime = "image/jpeg"
            return f"data:{mime};base64,{encoded}"
    except Exception as e:
        print("Image encode error:", e)
        return None

def find_scene_image(scene_index: int):
    """Find the most likely storyboard image for a scene (shot_1, shot_2, ...)"""
    folder = Path(f"storyboards/scene_{scene_index+1:02d}")
    if not folder.exists():
        return None
    # prefer shot_1.png then anything else
    for name in ["shot_1.png", "shot_1.jpg", "shot_1.jpeg", "shot_1.webp"]:
        p = folder / name
        if p.exists():
            return p
    # otherwise pick first image file found
    for p in folder.iterdir():
        if p.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            return p
    return None

def build_scene_text(scene: dict):
    """Construct dialogue/narration string for a scene"""
    parts = []
    summary = scene.get("summary", "")
    if summary:
        parts.append(f"Summary:\n{summary}")
    # try to extract dialogues from shots if present
    shots = scene.get("shots", [])
    if isinstance(shots, list) and shots:
        for s in shots:
            typ = s.get("type", "")
            desc = s.get("description", "")
            dlg = s.get("dialogue", "")
            if typ:
                parts.append(f"Shot: {typ}")
            if desc:
                parts.append(desc)
            if dlg:
                parts.append(f"\"{dlg}\"")
    # also include any explicit 'dialogue' key at scene level
    if "dialogue" in scene and scene.get("dialogue"):
        parts.append(scene.get("dialogue"))
    return "\n\n".join(parts).strip() or "No dialogue or narration available for this scene."

def handle_navigation_queryparams():
    """Check query params for navigation actions and update session_state.scene_idx"""
    params = st.experimental_get_query_params()
    action = params.get("action", [None])[0]
    if action:
        current = st.session_state.get("scene_idx", 0)
        total = len(st.session_state.breakdown.get("scenes", [])) if st.session_state.breakdown else 0
        if action == "next":
            new = min(current + 1, max(0, total - 1))
        elif action == "prev":
            new = max(0, current - 1)
        else:
            new = current
        # only update if changed
        if new != current:
            st.session_state.scene_idx = new
            # bump anim token to trigger CSS animation change
            st.session_state._anim_token = str(time.time())
        # clear params to avoid repeated navigation on rerun
        st.experimental_set_query_params()
        # rerun to reflect changes
        rerun()

# Configure the app
st.set_page_config(page_title="AI Director - Tamil", page_icon="🎬", layout="wide")

# Run startup cleanup
startup_cleanup()

# Initialize session state
if "script_text" not in st.session_state:
    st.session_state.script_text = ""
if "breakdown" not in st.session_state:
    st.session_state.breakdown = None
if "scene_images" not in st.session_state:
    st.session_state.scene_images = {}  # scene_number -> image path
if "scene_prompts" not in st.session_state:
    st.session_state.scene_prompts = {}

st.title("🎬 AI Director — தமிழ்")
st.markdown("---")

# ── Script Input ──────────────────────────────────────────
col_input, col_upload = st.columns([0.6, 0.4])

with col_input:
    st.subheader("📜 திரைக்கதை உள்ளீடு (Script Input)")
    script_text = st.text_area(
        "திரைக்கதையை இங்கே ஒட்டவும்",
        value=st.session_state.script_text,
        height=280,
        key="script_area",
        placeholder="உங்கள் தமிழ் திரைக்கதையை இங்கே ஒட்டவும்..."
    )
    if script_text != st.session_state.script_text:
        st.session_state.script_text = script_text

with col_upload:
    st.subheader("📂 கோப்பு பதிவேற்றம் (Upload)")
    uploaded_file = st.file_uploader(
        "Script file (txt / pdf / docx)",
        type=["txt", "pdf", "docx"],
        label_visibility="collapsed"
    )
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".txt"):
                loaded = uploaded_file.read().decode("utf-8")
            elif uploaded_file.name.endswith(".pdf"):
                pdf = PdfReader(uploaded_file)
                loaded = "\n".join(p.extract_text() or "" for p in pdf.pages)
            elif uploaded_file.name.endswith(".docx"):
                loaded = docx2txt.process(uploaded_file)
            else:
                loaded = ""
            st.session_state.script_text = loaded
            st.success(f"✅ '{uploaded_file.name}' ஏற்றப்பட்டது")
        except Exception as e:
            st.error(f"கோப்பு பிழை: {e}")

    st.markdown("&nbsp;", unsafe_allow_html=True)
    if st.button("🗑️ அனைத்தையும் அழி (Clear All)", use_container_width=True):
        clear_workspace_data()
        st.session_state.breakdown = None
        st.session_state.scene_images = {}
        st.session_state.scene_prompts = {}
        st.session_state.script_text = ""
        rerun()

# ── Generate Breakdown ────────────────────────────────────
col_btn, _ = st.columns([0.3, 0.7])
with col_btn:
    generate_btn = st.button("🔍 காட்சி பிரிப்பு உருவாக்கு (Generate Breakdown)",
                             type="primary", use_container_width=True)

if generate_btn:
    if not st.session_state.script_text.strip():
        st.warning("முதலில் திரைக்கதை உள்ளிடவும்.")
    else:
        script_prompt = LanguageManager.get_script_prompt('tamil')
        prompt_breakdown = (
            f"{script_prompt}\n\n"
            f"Script Text:\n{st.session_state.script_text}"
        )
        with st.spinner("திரைக்கதை பகுப்பாய்வு செய்கிறோம்..."):
            try:
                raw = safe_generate_content(prompt_breakdown)
                cleaned = re.sub(r"```(?:json)?\s*", "", raw or "").strip().rstrip("`").strip()
                parsed = extract_json_from_text(cleaned)
                if parsed and isinstance(parsed, dict) and "scenes" in parsed:
                    st.session_state.breakdown = parsed
                    st.session_state.scene_images = {}
                    with open("script_breakdown.json", "w", encoding="utf-8") as f:
                        json.dump(parsed, f, ensure_ascii=False, indent=4)
                    st.success(f"✅ {len(parsed['scenes'])} காட்சிகள் கண்டறியப்பட்டன!")
                else:
                    st.error("பகுப்பாய்வு தோல்வி. மீண்டும் முயற்சிக்கவும்.")
            except Exception as e:
                st.error(f"பிழை: {e}")

# Load from file if breakdown not in session
if not st.session_state.breakdown and Path("script_breakdown.json").exists():
    try:
        with open("script_breakdown.json", "r", encoding="utf-8") as f:
            st.session_state.breakdown = json.load(f)
    except Exception:
        pass

# ── Scene Cards ───────────────────────────────────────────
st.markdown("---")

if not st.session_state.breakdown:
    st.info("காட்சி பிரிப்பு இல்லை. மேலே 'Generate Breakdown' அழுத்தவும்.")
else:
    breakdown = st.session_state.breakdown
    scenes = breakdown.get("scenes", [])
    title = breakdown.get("title", "")
    if title:
        st.subheader(f"🎞️ {title}")

    for scene in scenes:
        sn = scene.get("scene_number", "?")
        location = scene.get("location", "")
        time_day = scene.get("time", "")
        weather = scene.get("weather", "")
        characters = scene.get("characters", [])
        props = scene.get("props", [])
        summary = scene.get("summary", "")
        audio = scene.get("audio", "")
        actions = scene.get("action", [])
        dialogues = scene.get("dialogues", [])

        header = f"காட்சி {sn}"
        if location:
            header += f" — {location}"
        if time_day:
            header += f" | {time_day}"
        if weather:
            header += f" | {weather}"

        with st.expander(header, expanded=True):
            # ── Meta row ──
            meta_cols = st.columns([1, 1, 1])
            with meta_cols[0]:
                if characters:
                    st.markdown("**👥 கதாபாத்திரங்கள்**")
                    for c in characters:
                        st.markdown(f"- {c}")
            with meta_cols[1]:
                if props:
                    st.markdown("**🎭 உபகரணங்கள் (Props)**")
                    for p in props:
                        st.markdown(f"- {p}")
            with meta_cols[2]:
                if audio:
                    st.markdown(f"**🎵 ஒலி:** {audio}")
                if summary:
                    st.markdown("**📝 சுருக்கம் (Summary)**")
                    st.caption(summary)

            # ── Action lines ──
            if actions:
                st.markdown("**🎬 நடவடிக்கைகள் (Action)**")
                for a in actions:
                    st.markdown(f"> {a}")

            # ── Dialogues + Shots ──
            available_shots = ["🎬 முதன்மை காட்சி (Master Dramatic Scene Shot)"]
            if dialogues:
                st.markdown("**💬 உரையாடல்கள் & ஷாட்கள் (Dialogues & Shots)**")
                for idx, dlg in enumerate(dialogues):
                    char = dlg.get("character", "")
                    line = dlg.get("line", "")
                    shots = dlg.get("shots", [])
                    st.markdown(f"**{char}:** {line}")
                    if shots:
                        for shot in shots:
                            st.markdown(f"&nbsp;&nbsp;&nbsp;📷 *{shot}*", unsafe_allow_html=True)
                            available_shots.append(f"📷 {shot} ({char})")
                    else:
                        fallback_shot = f"Close-up - {char} உணர்ச்சி மற்றும் உரையாடல் வெளிப்பாடு"
                        st.markdown(f"&nbsp;&nbsp;&nbsp;📷 *{fallback_shot}*", unsafe_allow_html=True)
                        available_shots.append(f"📷 {fallback_shot}")
                        available_shots.append(f"📷 Medium Shot - {char} இருவர் உரையாடல் மற்றும் நடவடிக்கை")

            # Remove duplicates preserving order
            seen = set()
            available_shots = [x for x in available_shots if not (x in seen or seen.add(x))]

            st.markdown("---")

            # ── Image area ──
            img_key = f"scene_{sn}"
            img_col, btn_col = st.columns([0.62, 0.38])

            with btn_col:
                selected_shot = st.selectbox(
                    "🎯 ஷாட் தேர்வு (Select Shot Framing)",
                    options=available_shots,
                    key=f"shot_sel_{sn}"
                )
                
                if st.button(f"🖼️ படம் உருவாக்கு\n(Generate Storyboard)", key=f"gen_{img_key}", use_container_width=True):
                    out_dir = Path(f"storyboards/scene_{sn:02d}" if isinstance(sn, int) else f"storyboards/scene_{sn}")
                    out_dir.mkdir(parents=True, exist_ok=True)
                    out_file = out_dir / "scene.png"

                    with st.spinner("முழு திரைக்கதை, உரையாடல் & ஷாட்டை பகுப்பாய்வு செய்து படம் உருவாக்குகிறோம்..."):
                        try:
                            # Intelligently synthesize prompt from all actions, weather, time, characters, and selected shot
                            image_prompt = build_cinematic_image_prompt(scene, selected_shot)
                            st.session_state.scene_prompts[img_key] = image_prompt
                            
                            success = generate_image(image_prompt, str(out_file))
                            if success and out_file.exists():
                                st.session_state.scene_images[img_key] = str(out_file)
                                st.success("✅ படம் தயார்!")
                                rerun()
                            else:
                                st.error("படம் உருவாக்க தோல்வி. மீண்டும் முயற்சிக்கவும்.")
                        except Exception as e:
                            st.error(f"பிழை: {e}")

            with img_col:
                saved_path = st.session_state.scene_images.get(img_key)
                if saved_path and Path(saved_path).exists():
                    st.image(saved_path, caption=f"காட்சி {sn} — உருவாக்கப்பட்ட படம்", use_container_width=True)
                    if img_key in st.session_state.scene_prompts:
                        with st.expander("👁️ AI ஒளிப்பதிவு விளக்கம் (Visual Prompt Used)"):
                            st.caption(st.session_state.scene_prompts[img_key])



