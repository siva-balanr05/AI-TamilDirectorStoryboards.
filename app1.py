import os
import json
import re
import shutil
from pathlib import Path
import streamlit as st
from streamlit import rerun
import docx2txt
from PyPDF2 import PdfReader
from src.model_utils import generate_text, generate_image
from src.language_utils import LanguageManager

# No API keys needed - using local models

def clear_workspace_data(startup=False):
    """Clear all generated files and reset the workspace"""
    try:
        # Clear storyboards directory
        shutil.rmtree('storyboards', ignore_errors=True)
        os.makedirs('storyboards/scene_01', exist_ok=True)
        
        # Remove script breakdown files
        if os.path.exists('tamil_script_breakdown.json'):
            os.remove('tamil_script_breakdown.json')
        if os.path.exists('tamil_shotlist.json'):
            os.remove('tamil_shotlist.json')
        
        # Clear session state on non-startup clears
        if not startup:
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
        return True
    except Exception as e:
        if not startup:  # Only show error if not during startup
            st.error(f"Error clearing workspace: {str(e)}")
        return False

def startup_cleanup():
    """Clean up old files on app startup"""
    # Check if this is the first run
    if 'initialized' not in st.session_state:
        clear_workspace_data(startup=True)
        st.session_state.initialized = True

# Configure the app
st.set_page_config(
    page_title="AI Director",
    page_icon="🎬",
    layout="wide"
)

# Run startup cleanup
startup_cleanup()

# Add page heading
st.title("🎬 AI Director")

# Initialize session state
if 'last_api_call' not in st.session_state:
    st.session_state.last_api_call = 0
if 'selected_language' not in st.session_state:
    st.session_state.selected_language = 'english'

# Language selector in sidebar
with st.sidebar:
    st.markdown("### 🌐 Language Settings")
    languages = LanguageManager.get_supported_languages()
    selected_lang = st.selectbox(
        "Choose Script Language",
        options=[lang['code'] for lang in languages],
        format_func=lambda x: next(lang['native_name'] for lang in languages if lang['code'] == x),
        index=[i for i, lang in enumerate(languages) if lang['code'] == st.session_state.selected_language][0]
    )
    st.session_state.selected_language = next(lang['name'].lower() for lang in languages if lang['code'] == selected_lang)

# -------------------------------------------------
# 🧠 Helper functions with rate limiting
# -------------------------------------------------
import time
from functools import wraps
import random

def retry_with_backoff(retries=3, backoff_in_seconds=1):
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
                    sleep = (backoff_in_seconds * 2 ** x + 
                            random.uniform(0, 1))
                    if "retry_delay" in str(e):
                        # Extract delay from Gemini error message
                        match = re.search(r'retry in (\d+\.?\d*)', str(e))
                        if match:
                            sleep = float(match.group(1)) + random.uniform(0.1, 1)
                    st.warning(f"API call failed, retrying in {sleep:.2f}s... ({x+1}/{retries})")
                    time.sleep(sleep)
                    x += 1
        return wrapper
    return decorator

@retry_with_backoff(retries=3, backoff_in_seconds=2)
def safe_generate_content(prompt: str) -> str:
    try:
        return generate_text(prompt)
    except Exception as e:
        st.error(f"Model call error: {e}")
        # Re-raise the exception for the retry decorator
        raise e

def extract_json_from_text(text: str):
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
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
                candidate = text[start: i + 1]
                try:
                    return json.loads(candidate)
                except Exception:
                    start = text.find("{", start + 1)
                    if start == -1:
                        return None
                    count = 0
    return None

def clear_workspace_data(startup=False):
    """Clear all generated files and reset the workspace"""
    try:
        # Clear storyboards directory
        shutil.rmtree('storyboards', ignore_errors=True)
        os.makedirs('storyboards/scene_01', exist_ok=True)
        
        # Remove script breakdown files
        if os.path.exists('tamil_script_breakdown.json'):
            os.remove('tamil_script_breakdown.json')
        if os.path.exists('tamil_shotlist.json'):
            os.remove('tamil_shotlist.json')
        
        # Clear session state on non-startup clears
        if not startup:
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
        return True
    except Exception as e:
        if not startup:  # Only show error if not during startup
            st.error(f"Error clearing workspace: {str(e)}")
        return False

# Add startup cleanup
def startup_cleanup():
    """Clean up old files on app startup"""
    # Check if this is the first run
    if 'initialized' not in st.session_state:
        clear_workspace_data(startup=True)
        st.session_state.initialized = True

def safe_intensity(value, default=5):
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        match = re.search(r"\d+", value)
        if match:
            return int(match.group())
    return default

# -------------------------------------------------
# 🧠 Domain helper functions
# -------------------------------------------------
def suggest_cinematic_shots(scene_data: dict) -> list:
    shot_prompt = LanguageManager.get_shot_prompt(st.session_state.selected_language)
    
    prompt = f"""
{shot_prompt}

Scene Details:
- Location: {scene_data.get('location', '')}
- Characters: {', '.join(scene_data.get('characters', []))}
- Props: {', '.join(scene_data.get('props', []))}
- Summary: {scene_data.get('summary', '')}
"""
    response = safe_generate_content(prompt)
    shots_data = extract_json_from_text(response)
    return shots_data.get('shots', []) if shots_data else []

def analyze_dialogue(dialogue: str) -> dict:
    """Analyze the emotional content of a dialogue."""
    try:
        # Safely get the selected language from session state
        language = st.session_state.get("selected_language", "english")
        
        # Build the prompt
        prompt = (
            f"Analyze this dialogue in {language}:\n\n"
            f"Dialogue: {dialogue}\n\n"
            "Respond in JSON format:\n"
            "{\n"
            '    "emotion": "happiness/anger/sadness/fear/surprise",\n'
            '    "intensity": "1 to 10",\n'
            '    "tone": "normal/intense/humorous/frustrated"\n'
            "}"
        )

        # Call your model to analyze dialogue
        response = generate_text(prompt)
        result = extract_json_from_text(response)

        # Return default if parsing fails
        if not result:
            return {"emotion": "neutral", "intensity": 5, "tone": "normal"}
        return result

    except Exception as e:
        print(f"⚠️ Dialogue analysis error: {e}")
        return {"emotion": "neutral", "intensity": 5, "tone": "normal"}


def get_camera_angles(emotion: str, intensity: int, tone: str) -> list:
    angle_map = {
        "happiness": ["Medium Shot", "Tracking Shot", "High Angle"],
        "anger": ["Close-up", "Dutch Angle", "Steadicam Shot"],
        "sadness": ["Extreme Close-up", "High Angle", "Slow Tracking Shot"]
    }
    base_angles = angle_map.get(emotion.lower(), ["Medium Shot", "Close-up"])
    if intensity >= 8:
        base_angles.extend(["எக்ஸ்ட்ரீம் க்ளோஸ்-அப்", "டச் ஆங்கிள்"])
    elif intensity <= 3:
        base_angles.extend(["லாங் ஷாட்", "ஸ்டெடிகேம் ஷாட்"])
    return base_angles

@retry_with_backoff(retries=3, backoff_in_seconds=2)
def translate_to_english(text: str) -> str:
    """
    Detects the language automatically and translates to cinematic English
    for AI image generation prompts.
    """
    if not text or not text.strip():
        return ""

    time.sleep(1)  # prevent rate-limit issues
    prompt = f"""
You are a multilingual film translator AI.
Detect the input language and translate it into professional cinematic English,
suitable for use as an AI image generation prompt.
Do not include explanations — only give the short, cinematic English phrase.

Text:
{text}
"""
    try:
        result = safe_generate_content(prompt).strip()
        if not result:
            st.warning(f"Translation failed for: {text[:50]}...")
            return text.strip()
        return result
    except Exception as e:
        st.error(f"Translation error: {e}")
        return text.strip()


def clean_prompt(text: str, max_len: int = 1900) -> str:
    text = text.replace("```", "").strip()
    text = " ".join(line.strip() for line in text.split("\n") if line.strip())
    if len(text) > max_len:
        text = text[: max_len - 3] + "..."
    return text

# -------------------------------------------------
# 🖼️ Local Qwen Image Generation
# -------------------------------------------------
def ensure_english(text: str) -> str:
    """Ensure text is in English by translating if needed."""
    # Check if text contains non-ASCII characters (potentially Tamil)
    if any(ord(char) > 127 for char in text):
        return translate_to_english(text)
    return text

def generate_image(prompt: str, output_file: Path) -> str | None:
    """Generate storyboard image with Qwen Image model and return saved path or None."""
    if not prompt.strip():
        st.error("Prompt is empty!")
        return None

    # Ensure prompt is in English
    english_prompt = ensure_english(prompt)
    st.info(f"Translated prompt: {english_prompt}")

    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        if generate_image(english_prompt, str(output_file)):
            return str(output_file)
        else:
            st.error("Failed to generate image")
            return None
    except Exception as e:
        st.error(f"Failed to generate or save image: {str(e)}")
        return None


# -------------------------------------------------
# Streamlit page
# -------------------------------------------------
st.set_page_config(page_title="Director's Dashboard", layout="wide")
st.title("🎬 Director's Dashboard — Breakdown → Shots → Storyboards")

if "breakdown" not in st.session_state:
    st.session_state["breakdown"] = None
if "dialogue_cache" not in st.session_state:
    st.session_state["dialogue_cache"] = {}
if "script_text" not in st.session_state:
    st.session_state["script_text"] = ""

# Rest of your Streamlit UI code remains the same as before
# (Left/Right columns, script upload, scene selection, emotion analysis,
# storyboard generation) using generate_image() function above




# -------------------------------------------------
# Streamlit page config
# -------------------------------------------------
st.set_page_config(page_title="Director's Dashboard", layout="wide")


# Sidebar controls
with st.sidebar:
    # Language Settings
    st.markdown("### 🌐 Language Settings")
    languages = LanguageManager.get_supported_languages()
    selected_lang = st.selectbox(
        "Choose Script Language",
        options=[lang['code'] for lang in languages],
        format_func=lambda x: next(lang['native_name'] for lang in languages if lang['code'] == x),
        index=[i for i, lang in enumerate(languages) if lang['code'] == st.session_state.get('selected_language', 'en')][0]
    )
    st.session_state.selected_language = next(lang['name'].lower() for lang in languages if lang['code'] == selected_lang)
    
    # Workspace Controls
    st.markdown("### 🧹 Workspace Controls")
    
    # Use two columns for the clear button and confirmation
    clear_col1, clear_col2 = st.columns([3, 2])
    
    with clear_col1:
        clear_button = st.button("🗑️ Clear All Data", 
                               help="This will remove all generated files and reset the workspace",
                               type="secondary")
    
    if clear_button:
        with clear_col2:
            if st.button("✓ Confirm", type="primary"):
                if clear_workspace_data():
                    st.success("✨ Workspace cleared successfully!")
                    time.sleep(1)  # Give time for the message to show
                    st.experimental_rerun()  # Refresh the page

if "breakdown" not in st.session_state:
    st.session_state["breakdown"] = None
if "dialogue_cache" not in st.session_state:
    st.session_state["dialogue_cache"] = {}
if "script_text" not in st.session_state:
    st.session_state["script_text"] = ""  # Initialize script text storage

# Main UI layout
col_left, col_right = st.columns([0.4, 0.6])

with col_left:
    st.subheader("📜 Script Input")
    script_text = st.text_area(
        "Enter or paste your script here", 
        value=st.session_state.script_text,
        height=400,
        key="script_area"
    )
    
    # Auto-detect language when script is entered
    if script_text != st.session_state.script_text:
        st.session_state.script_text = script_text
        if script_text.strip():
            detected_lang = LanguageManager.detect_script_language(script_text)
            st.session_state.selected_language = detected_lang
            st.info(f"📢 Detected script language: {detected_lang.title()}")

    if st.button("🔍 Generate Breakdown"):
        script_prompt = LanguageManager.get_script_prompt(st.session_state.selected_language)
        
        prompt_breakdown = (
            f"{script_prompt}\n\n"
            f"Script Text:\n{script_text}\n\n"
            "Return the analysis in JSON format with scenes, locations, characters, etc."
        )

        with st.spinner("Analyzing script..."):
            raw = safe_generate_content(prompt_breakdown)
            parsed = extract_json_from_text(raw)
            if parsed and isinstance(parsed, dict) and "scenes" in parsed:
                st.session_state.breakdown = parsed
                with open("script_breakdown.json", "w", encoding="utf-8") as f:
                    json.dump(parsed, f, ensure_ascii=False, indent=4)
                st.success("✅ Script breakdown generated!")
            else:
                st.error("Failed to analyze script. Please try again.")

    if st.session_state["breakdown"] is None and Path("script_breakdown.json").exists():
        try:
            with open("script_breakdown.json", "r", encoding="utf-8") as f:
                st.session_state["breakdown"] = json.load(f)
        except Exception as e:
            st.error(f"Failed to load existing breakdown file: {e}")

    st.markdown("---")
    st.caption("Tip: Select a scene on the right panel to generate shots & storyboards for that scene only.")

# -------------------------------------------------
# UI — Right Column
# -------------------------------------------------
with col_right:
    uploaded_file = st.file_uploader("📂 Upload Script (txt/pdf/docx/json)", type=["txt", "pdf", "docx", "json"])

    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".json"):
                bd = json.load(uploaded_file)
                st.session_state["breakdown"] = bd
                st.success("✅ Script breakdown loaded from JSON.")
            else:
                if uploaded_file.name.endswith(".txt"):
                    st.session_state["script_text"] = uploaded_file.read().decode("utf-8")
                elif uploaded_file.name.endswith(".pdf"):
                    pdf_reader = PdfReader(uploaded_file)
                    st.session_state["script_text"] = "\n".join(
                        page.extract_text() for page in pdf_reader.pages if page.extract_text()
                    )
                elif uploaded_file.name.endswith(".docx"):
                    st.session_state["script_text"] = docx2txt.process(uploaded_file)
                else:
                    st.error("Unsupported file format.")
                    st.session_state["script_text"] = ""

                if st.session_state["script_text"].strip():
                    st.success("✅ Script loaded successfully. You can now generate breakdown from left panel.")
                else:
                    st.error("No text found in uploaded file.")
        except Exception as e:
            st.error(f"❌ Failed to process uploaded file: {e}")

    bd = st.session_state.get("breakdown")
    if not bd or "scenes" not in bd or len(bd["scenes"]) == 0:
        st.info(" Generate breakdown from left panel or upload a JSON file.")
    else:
        scenes = sorted(bd["scenes"], key=lambda x: int(x.get("scene_number", 0)))
        scene_numbers = [int(s.get("scene_number", idx + 1)) for idx, s in enumerate(scenes)]
        selected_scene_number = st.selectbox("🎥 Select scene", scene_numbers)
        scene = next((s for s in scenes if int(s.get("scene_number", 0)) == int(selected_scene_number)), scenes[0])

        st.subheader(f"📖 Scene {selected_scene_number} — Breakdown")
        st.write(f"**Location:** {scene.get('location', '')}")
        st.write(f"**Characters:** {', '.join(scene.get('characters', []))}")
        st.write(f"**Props:** {', '.join(scene.get('props', []))}")
        st.write(f"**Summary:** {scene.get('summary', '')}")
        
        # Get cinematic shot suggestions
        cinematic_shots = suggest_cinematic_shots(scene)
        
        # Display cinematographer's suggestions
        if cinematic_shots:
            st.markdown("### 📽️ சினிமாடோகிராபர் பரிந்துரைகள்")
            for i, shot in enumerate(cinematic_shots, 1):
                with st.expander(f"🎬 ஷாட் {i}: {shot.get('type', '')}"):
                    st.write(f"**விளக்கம்:** {shot.get('description', '')}")
                    if shot.get('camera_movement'):
                        st.write(f"**கேமரா இயக்கம்:** {shot.get('camera_movement')}")
                    st.write(f"**ஒளி அமைப்பு:** {shot.get('lighting', '')}")
                    
                    # Add Generate Storyboard button for this specific shot
                    if st.button(f"🎨 Generate Storyboard", key=f"cinematographer_shot_{selected_scene_number}_{i}"):
                        with st.spinner(f"Generating storyboard for shot {i}..."):
                            output_dir = Path(f"storyboards/scene_{int(selected_scene_number):02d}")
                            output_dir.mkdir(parents=True, exist_ok=True)
                            
                            # Translate all components to English
                            translated_shot_type = translate_to_english(shot.get('type', ''))
                            translated_description = translate_to_english(shot.get('description', ''))
                            translated_movement = translate_to_english(shot.get('camera_movement', ''))
                            translated_lighting = translate_to_english(shot.get('lighting', ''))
                            location_en = translate_to_english(scene.get('location', ''))
                            summary_en = translate_to_english(scene.get('summary', ''))
                            props_en = [translate_to_english(p) for p in scene.get('props', [])]
                            chars_en = [translate_to_english(c) for c in scene.get('characters', [])]
                            
                            # Create a detailed cinematic prompt
                            storyboard_prompt = (
                                f"Create a cinematic storyboard visual for:\n"
                                f"Shot Type: {translated_shot_type}\n"
                                f"Scene Description: {translated_description}\n"
                                f"Camera Movement: {translated_movement}\n"
                                f"Lighting Setup: {translated_lighting}\n"
                                f"Location: {location_en}\n"
                                f"Scene Context: {summary_en}\n"
                                f"Props: {', '.join(props_en)}\n"
                                f"Characters: {', '.join(chars_en)}\n"
                                f"Style: Professional cinematic composition, dramatic lighting, "
                                f"high production value, photorealistic, movie storyboard style."
                            )
                            
                            english_prompt = clean_prompt(storyboard_prompt)
                            filename = output_dir / f"cinematographer_shot_{i}.png"
                            
                            if generate_image(english_prompt, filename):
                                # Save metadata
                                metadata_file = output_dir / f"cinematographer_shot_{i}.json"
                                with open(metadata_file, "w", encoding="utf-8") as mf:
                                    json.dump({
                                        "shot_type": shot.get("type"),
                                        "description": shot.get("description"),
                                        "camera_movement": shot.get("camera_movement"),
                                        "lighting": shot.get("lighting"),
                                        "prompt_english": english_prompt,
                                        "image_file": str(filename)
                                    }, mf, ensure_ascii=False, indent=4)
                                st.success(f"✅ Storyboard generated for shot {i}!")
                                
                                # Display the generated image
                                st.image(str(filename), caption=f"Generated Storyboard - Shot {i}", use_column_width=True)
                                with open(filename, "rb") as f:
                                    st.download_button(
                                        label=f"⬇️ Download Storyboard {i}",
                                        data=f,
                                        file_name=filename.name,
                                        mime="image/png"
                                    )

        st.divider()
        st.subheader("💬 Dialogues & Shots")

        col_scene_actions = st.columns([1, 1, 1])
        if col_scene_actions[0].button("🔁 Regenerate Emotion+Angles for Scene"):
            with st.spinner("Analyzing dialogues (with rate limiting)..."):
                total_dialogues = len(scene.get("dialogues", []))
                progress_bar = st.progress(0)
                
                for d_idx, dialogue in enumerate(scene.get("dialogues", []), start=1):
                    key = (int(selected_scene_number), d_idx)
                    st.info(f"Processing dialogue {d_idx}/{total_dialogues}...")
                    
                    # Add delay between API calls to avoid rate limits
                    if d_idx > 1:
                        time.sleep(2)
                    
                    ed = {
                        "emotion": "neutral",
                        "intensity": 5,
                        "tone": "normal",
                        "subtext": ""
                    }
                    
                    try:
                        ed = analyze_dialogue(dialogue.get("line", ""))
                    except Exception as e:
                        st.error(f"Error analyzing dialogue {d_idx}: {str(e)}")
                    
                    angles = get_camera_angles(
                        ed.get("emotion", "neutral"),
                        safe_intensity(ed.get("intensity", 5)),
                        ed.get("tone", "normal")
                    )
                    
                    # Cache the results
                    st.session_state["dialogue_cache"][key] = {
                        "emotion_data": ed,
                        "angles": angles,
                        "translated": ""  # Will be translated when needed
                    }
                    dialogue["emotion_data"] = ed
                    dialogue["suggested_angles"] = angles
                    
                    # Update progress
                    progress_bar.progress(d_idx / total_dialogues)
                    ed.get("emotion", "neutral"),
                    safe_intensity(ed.get("intensity", 5)),
                    ed.get("tone", "normal")
                    st.session_state["dialogue_cache"][key] = {
                        "emotion_data": ed,
                        "angles": angles,
                        "translated": translate_to_english(dialogue.get("line", "")),
                    }
                    dialogue["emotion_data"] = ed
                    dialogue["suggested_angles"] = angles

                with open("tamil_script_breakdown.json", "w", encoding="utf-8") as f:
                    json.dump(st.session_state["breakdown"], f, ensure_ascii=False, indent=4)
                st.success("✅ Emotion & angles updated for scene.")

        if col_scene_actions[1].button("🎨 Generate Storyboards for Scene"):
            with st.spinner("Generating scene storyboards..."):
                scene_num = int(selected_scene_number)
                output_dir = Path(f"storyboards/scene_{scene_num:02d}")
                output_dir.mkdir(parents=True, exist_ok=True)
                for d_idx, dialogue in enumerate(scene.get("dialogues", []), start=1):
                    key = (int(selected_scene_number), d_idx)
                    cache = st.session_state["dialogue_cache"].get(key)
                    if not cache:
                        ed = dialogue.get("emotion_data") or analyze_dialogue(dialogue.get("line", ""))
                        angles = dialogue.get("suggested_angles") or get_camera_angles(
                            ed.get("emotion", "neutral"),
                            safe_intensity(ed.get("intensity", 5)),
                            ed.get("tone", "normal"),
                        )
                        translated = translate_to_english(dialogue.get("line", ""))
                        cache = {"emotion_data": ed, "angles": angles, "translated": translated}
                        st.session_state["dialogue_cache"][key] = cache
                    for s_idx, shot in enumerate(cache["angles"], start=1):
                        translated_shot = translate_to_english(shot)
                        # Translate all Tamil components to English
                        location_en = translate_to_english(scene.get('location', ''))
                        summary_en = translate_to_english(scene.get('summary', ''))
                        props_en = [translate_to_english(p) for p in scene.get('props', [])]
                        chars_en = [translate_to_english(c) for c in scene.get('characters', [])]
                        character_en = translate_to_english(dialogue.get('character', ''))
                        emotion_en = translate_to_english(cache['emotion_data'].get('emotion', ''))
                        tone_en = translate_to_english(cache['emotion_data'].get('tone', ''))
                        
                        storyboard_prompt = (
                            f"Cinematic storyboard: {translated_shot}. "
                            f"Location: {location_en}. "
                            f"Scene summary: {summary_en}. "
                            f"Props: {', '.join(props_en)}. "
                            f"Characters: {', '.join(chars_en)}. "
                            f"Shot: {translated_shot}. "
                            f"{character_en} says: {cache['translated']}. "
                            f"Emotion: {emotion_en} "
                            f"(intensity {cache['emotion_data'].get('intensity')}/10), tone: {tone_en}. "
                            f"Dramatic lighting, professional camera work, cinematic composition, no text."
                        )
                        english_prompt = clean_prompt(storyboard_prompt)
                        filename = output_dir / f"dialogue{d_idx}_shot{s_idx}.png"
                        generate_image(english_prompt, filename)
                        metadata_file = output_dir / f"dialogue{d_idx}_shot{s_idx}.json"
                        with open(metadata_file, "w", encoding="utf-8") as mf:
                            json.dump({
                                "character": dialogue.get("character"),
                                "dialogue_tamil": dialogue.get("line"),
                                "shot_tamil": shot,
                                "prompt_english": english_prompt,
                                "image_file": str(filename),
                            }, mf, ensure_ascii=False, indent=4)
                st.success("✅ Storyboards generated for selected scene.")
                rerun()

        output_dir = Path(f"storyboards/scene_{int(selected_scene_number):02d}")
        if output_dir.exists():
            for img_file in sorted(output_dir.glob("*.png")):
                st.image(str(img_file), caption=img_file.name)
                with open(img_file, "rb") as f:
                    st.download_button(
                        label=f"⬇️ Download {img_file.name}",
                        data=f,
                        file_name=img_file.name,
                        mime="image/png"
                    )

        for d_idx, dialogue in enumerate(scene.get("dialogues", []), start=1):
            with st.expander(f"💬 Dialogue {d_idx}: {dialogue.get('character','unknown')}"):
                st.write(dialogue.get("line", ""))
                key = (int(selected_scene_number), d_idx)
                cache = st.session_state["dialogue_cache"].get(key)
                if not cache:
                    ed = dialogue.get("emotion_data") or analyze_dialogue(dialogue.get("line", ""))
                    angles = dialogue.get("suggested_angles") or get_camera_angles(
                        ed.get("emotion", "neutral"),
                        safe_intensity(ed.get("intensity", 5)),
                        ed.get("tone", "normal"),
                    )
                    translated = translate_to_english(dialogue.get("line", ""))
                    cache = {"emotion_data": ed, "angles": angles, "translated": translated}
                    st.session_state["dialogue_cache"][key] = cache
                    dialogue["emotion_data"] = ed
                    dialogue["suggested_angles"] = angles

                st.markdown("**Emotion Analysis:**")
                st.write(f"- Emotion: {cache['emotion_data'].get('emotion')}")
                st.write(f"- Intensity: {cache['emotion_data'].get('intensity')}/10")
                st.write(f"- Tone: {cache['emotion_data'].get('tone')}")

                st.markdown("**Camera Angles & Storyboard Generation:**")
                
                # Create columns for each camera angle with its own generate button
                angle_cols = st.columns(len(cache["angles"]))
                for col_idx, (angle, col) in enumerate(zip(cache["angles"], angle_cols), 1):
                    with col:
                        st.markdown(f"**Shot {col_idx}:** {angle}")
                        if st.button(f"🎨 Generate Shot {col_idx}", key=f"shot_{selected_scene_number}_{d_idx}_{col_idx}"):
                            with st.spinner(f"Generating shot {col_idx} for dialogue {d_idx}..."):
                                scene_num = int(selected_scene_number)
                                output_dir = Path(f"storyboards/scene_{scene_num:02d}")
                                output_dir.mkdir(parents=True, exist_ok=True)

                                # Translate all components to English
                                translated_shot = translate_to_english(angle)
                                location_en = translate_to_english(scene.get('location', ''))
                                summary_en = translate_to_english(scene.get('summary', ''))
                                props_en = [translate_to_english(p) for p in scene.get('props', [])]
                                chars_en = [translate_to_english(c) for c in scene.get('characters', [])]
                                character_en = translate_to_english(dialogue.get('character', ''))
                                emotion_en = translate_to_english(cache['emotion_data'].get('emotion', ''))
                                tone_en = translate_to_english(cache['emotion_data'].get('tone', ''))

                                storyboard_prompt = (
                                    f"Cinematic storyboard: {translated_shot}. "
                                    f"Location: {location_en}. "
                                    f"Scene summary: {summary_en}. "
                                    f"Props: {', '.join(props_en)}. "
                                    f"Characters: {', '.join(chars_en)}. "
                                    f"Shot: {translated_shot}. "
                                    f"{character_en} says: {cache['translated']}. "
                                    f"Emotion: {emotion_en} "
                                    f"(intensity {cache['emotion_data'].get('intensity')}/10), tone: {tone_en}. "
                                    f"Dramatic lighting, professional camera work, cinematic composition, no text."
                                )
                                english_prompt = clean_prompt(storyboard_prompt)
                                filename = output_dir / f"dialogue{d_idx}_shot{col_idx}.png"
                                saved_file = generate_image(english_prompt, filename)
                                if saved_file:
                                    metadata_file = output_dir / f"dialogue{d_idx}_shot{col_idx}.json"
                                    with open(metadata_file, "w", encoding="utf-8") as mf:
                                        json.dump({
                                            "character": dialogue.get("character"),
                                            "dialogue_tamil": dialogue.get("line"),
                                            "shot_tamil": angle,
                                            "prompt_english": english_prompt,
                                            "image_file": str(filename),
                                        }, mf, ensure_ascii=False, indent=4)
                                    st.success(f"✅ Shot {col_idx} generated successfully!")
                
                # Display existing shots for this dialogue
                dialogue_shots = sorted(output_dir.glob(f"dialogue{d_idx}_shot*.png"))
                if dialogue_shots:
                    st.markdown("**Generated Shots:**")
                    shot_cols = st.columns(len(dialogue_shots))
                    for shot_file, shot_col in zip(dialogue_shots, shot_cols):
                        with shot_col:
                            st.image(str(shot_file), caption=shot_file.name, use_column_width=True)
                            with open(shot_file, "rb") as f:
                                st.download_button(
                                    label=f"⬇️ Download",
                                    data=f,
                                    file_name=shot_file.name,
                                    mime="image/png"
                                )
