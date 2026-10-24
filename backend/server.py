import os
import json
import re
import shutil
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import docx2txt
from PyPDF2 import PdfReader

from src.model_utils import generate_text, generate_image, build_cinematic_image_prompt
from src.language_utils import LanguageManager

app = FastAPI(title="AI Director API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
STORYBOARDS_DIR = WORKSPACE_ROOT / "storyboards"
BREAKDOWN_FILE = WORKSPACE_ROOT / "script_breakdown.json"

class BreakdownRequest(BaseModel):
    script_text: str
    language: Optional[str] = "tamil"

class GenerateImageRequest(BaseModel):
    scene: Dict[str, Any]
    shot: Optional[str] = None

def extract_json_from_text(text: str) -> Optional[dict]:
    """Extract JSON object from text with robust fallback"""
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
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

SAMPLE_SCRIPTS = [
    {
        "id": "drama-3-scenes",
        "title": "நம்பிக்கையின் பாதை (Emotional Drama - 3 Scenes)",
        "language": "tamil",
        "text": """தலைப்பு: நம்பிக்கையின் பாதை

அதிகாலை வேளையில் மதுரையின் அமைதியான கிராமத்து ரயில் நிலையத்தில் பனி மூட்டம் படர்ந்திருந்தது. தண்டவாளத்தில் இருந்து குளிர்ந்த காற்று வீசுகிறது. மேடையில் ஒரு பழைய இரும்பு பெஞ்ச் மீது பெரிய பை ஒன்று வைக்கப்பட்டுள்ளது. 

வேலன் தன் தாய் மீனாட்சியின் காலில் விழுந்து ஆசீர்வாதம் வாங்குகிறான். மீனாட்சி கண்ணீருடன் தன் மகனை எழுப்பி, ஒரு பித்தளை டிபன் பாக்ஸை அவன் கையில் கொடுத்து, "சென்னையில பெரிய போலீஸ் அதிகாரியா ஆகி திரும்பி வரணும் வேலன்... நேர்மைய மட்டும் எப்பவும் விட்றாதே" என்று சொல்கிறாள். வேலன் அவளது கைகளைப் பிடித்து, "கண்டிப்பா அம்மா, உங்க கனவை நான் நிறைவேற்றுவேன்" என்கிறான். தூரத்தில் புகையை கக்கிக்கொண்டு ரயில் ஹாரன் அடித்து மெதுவாக பிளாட்பாரத்திற்குள் நுழைகிறது. வேலன் ரயிலில் ஏறி ஜன்னல் வழியே தாயைப் பார்த்து கையசைக்கிறான்.

மறுநாள் மதியம் சென்னையின் நெரிசலான பாரிமுனை வீதி. வாகனங்களின் தொடர் சத்தம், மக்களின் கூச்சல், கடுமையான வெயில் தகித்துக் கொண்டிருந்தது. வேலன் தன் கனத்த தோள்பையை சுமந்து கொண்டு முகவரியை காகிதத்தில் தேடியபடி நடந்து செல்கிறான். திடீரென கந்தல் ஆடை அணிந்த ஒரு சிறுவன் மின்னல் வேகத்தில் ஓடிவந்து வேலனின் கையில் இருந்த பணப்பையையும் சான்றிதழ் கோப்பையும் பறித்துக்கொண்டு கூட்ட நெரிசலில் ஓடுகிறான். வேலன் அதிர்ச்சியடைந்து, "டேய் நில்லு! திருடன்... திருடன்... அந்த பையை விட்டுட்டு ஓடு!" என்று கத்தியபடி அவனை துரத்துகிறான். சிறுவன் காய்கறி கடைகள் மற்றும் ஆட்டோக்களுக்கு இடையே புகுந்து வளைந்து நெளிந்து ஓடுகிறான்.

இரவு நேரம். துறைமுகத்திற்கு அருகிலுள்ள ஒரு பாழடைந்த பழைய கிடங்கு. வெளியே சடசடவென பலத்த மழை பெய்கிறது. இடி மின்னலின் வெளிச்சம் பழைய உடைந்த ஜன்னல்கள் வழியாக உள்ளே விழுகிறது. ஓடிவந்த சிறுவன் மூச்சிரைக்க ஒரு மூலையில் சுருண்டு அமர்ந்திருக்கிறான். வேலன் கதவை உதைத்து உள்ளே நுழைகிறான். "பையை கீழே போடுடா!" என்று கோபத்துடன் சத்தமிடுகிறான். 

சிறுவன் பயத்தில் நடுங்கி அழத் தொடங்குகிறான். "அண்ணா என்னை அடிச்சிடாதீங்க... என் தங்கச்சிக்கு உடம்பு சரியில்லை, மருந்து வாங்கத்தான் இப்படி பண்ணிட்டேன்" என்று தரையில் படுத்திருக்கும் சிறுமியை கண்ணீருடன் காட்டுகிறான். அங்கே பழைய சாக்குப்பையில் ஒரு சிறுமி காய்ச்சலில் நடுங்கிக்கொண்டிருக்கிறாள். வேலனின் கோபம் மறைந்து கண்களில் கருணை வழிகிறது. வேலன் மெதுவாக சிறுவனின் தலையை வருடி, "பயப்படாதே... உன் தங்கச்சிக்கு எதுவும் ஆகாது, நான் பார்த்துக்கிறேன்" என்று கூறி தன் சட்டைப் பையிலிருந்த பணத்தை எடுத்து நீட்டுகிறான். கிடங்கின் பழைய விளக்கு காற்றில் மெதுவாக ஊசலாடுகிறது."""
    },
    {
        "id": "thriller-interrogation",
        "title": "கடைசி விசாரணை (Crime Thriller - Interrogation)",
        "language": "tamil",
        "text": """தலைப்பு: கடைசி விசாரணை

காட்சி 1: பழைய காவல் நிலைய விசாரணை அறை – இரவு
அறையில் ஒரே ஒரு மேஜை மற்றும் இரண்டு நாற்காலிகள். மேலே தொங்கும் பழைய மின்விளக்கு மங்கலாக ஊசலாடுகிறது. வெளியே இடி மின்னலுடன் பலத்த மழை பெய்கிறது.

இன்ஸ்பெக்டர் கார்த்திக் (40) கையில் ஒரு பழைய கோப்புடன் நின்று கொண்டிருக்கிறான். எதிரில் ரகுநாத் (35) கைவிலங்குடன் அமர்ந்திருக்கிறான்.

கார்த்திக்: (கோப்பை மேஜையில் வீசி) மூன்று வருடமா உன்னைத் தான் தேடிட்டு இருந்தேன் ரகுநாத். அந்த மர்ம பெட்டி எங்க?
ரகுநாத்: (சிரித்துக்கொண்டே) சட்டம் என்னை குற்றவாளின்னு நிரூபிக்க முடியாது சார். எனக்கு எதுவும் தெரியாது.
கார்த்திக்: (ரகுநாத்தின் முகத்தருகே குனிந்து) என் முன்னாடி நாடகமாடாதே! அந்த புகைப்படத்துல இருக்கிறது உன் தம்பி தானே?
ரகுநாத்: (திடுக்கிட்டு, கண்களில் பயத்துடன்) கார்த்திக் சார்... என் குடும்பத்தை இதுக்குள்ள இழுக்காதீங்க!
கார்த்திக்: அப்போ உண்மையை சொல்லு! 

மின்னல் வெளிச்சம் ஜன்னல் வழியே கார்த்திக்கின் முகத்தில் விழுகிறது. ரகுநாத்தின் கைகள் நடுங்குகின்றன."""
    },
    {
        "id": "tea-stall-farewell",
        "title": "மறந்தாலும் நான் (Romantic Drama - Tea Stall)",
        "language": "tamil",
        "text": """தலைப்பு: மறந்தாலும் நான்

காட்சி 1: சிறிய தேநீர் கடை – மாலை
வெளியே தூறல் மழை பெய்கிறது, பழைய ரேடியோவில் இளையராஜா பாடல் மெல்லிய ஒலியில் ஒலிக்கிறது. மேசையில் இரண்டு தேநீர் கோப்பைகள் உள்ளன. 
அருண் (25, இளைஞன்) தேநீர் கோப்பையை தயக்கத்துடன் கலக்கிக்கொண்டிருக்கிறான். எதிரில் மீனா (23, பெண்) அமைதியாக அமர்ந்திருக்கிறாள்.

அருண்: மீனா... தேர்வு முடிந்ததும் நான் சென்னைக்கு கிளம்புறேன். சாப்ட்வேர் நிறுவனத்தில் வேலை கிடைச்சிருக்கு.
மீனா: (மெல்லிய புன்னகையுடன்) அதுதானே உன் ஆசை, உன் கனவு. வாழ்த்துகள் அருண்.
அருண்: ஆனால்... உன்னை பிரிந்து போக என் மனசு வரல மீனா. நீ இல்லாத வாழ்க்கை வெறுமையாக இருக்கும்.
மீனா: உன் எதிர்காலம் தான் முதல்ல முக்கியம் அருண். என்னைப் பற்றி அப்புறம் யோசிக்கலாம்.
அருண்: நான் உன்னை எப்பவும் மறக்க மாட்டேன் மீனா... நீயும் என் கனவுதான்.

மழை வேகம் எடுக்கிறது. அருண் தலையை குனிகிறான், மீனா ஜன்னல் வழியே மழையைப் பார்க்கிறாள். கேமரா மெதுவாக பின்வாங்குகிறது."""
    }
]

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "AI Director 2.0 Web API"}

@app.get("/api/sample-scripts")
def get_sample_scripts():
    return SAMPLE_SCRIPTS

@app.get("/api/breakdown")
def get_existing_breakdown():
    if BREAKDOWN_FILE.exists():
        try:
            with open(BREAKDOWN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {"success": True, "breakdown": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return {"success": False, "breakdown": None}

@app.post("/api/breakdown")
def generate_breakdown(req: BreakdownRequest):
    script_text = req.script_text.strip()
    if not script_text:
        raise HTTPException(status_code=400, detail="Script text cannot be empty")
    
    lang = req.language or "tamil"
    script_prompt = LanguageManager.get_script_prompt(lang)
    prompt = f"{script_prompt}\n\nScript Text:\n{script_text}"
    
    try:
        raw = generate_text(prompt)
        cleaned = re.sub(r"```(?:json)?\s*", "", raw or "").strip().rstrip("`").strip()
        parsed = extract_json_from_text(cleaned)
        
        if not parsed or not isinstance(parsed, dict) or "scenes" not in parsed:
            raise HTTPException(status_code=422, detail="Failed to parse structured scene JSON from LLM")
            
        with open(BREAKDOWN_FILE, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=4)
            
        return {"success": True, "breakdown": parsed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Breakdown analysis error: {str(e)}")

@app.post("/api/upload-script")
async def upload_script_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        filename = file.filename.lower()
        extracted_text = ""
        
        if filename.endswith(".txt"):
            extracted_text = content.decode("utf-8", errors="replace")
        elif filename.endswith(".pdf"):
            import io
            pdf = PdfReader(io.BytesIO(content))
            extracted_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
        elif filename.endswith(".docx"):
            import io
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            extracted_text = docx2txt.process(tmp_path)
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        else:
            raise HTTPException(status_code=400, detail="Only .txt, .pdf, and .docx formats are supported")
            
        return {"filename": file.filename, "text": extracted_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@app.post("/api/generate-image")
def api_generate_image(req: GenerateImageRequest):
    scene = req.scene
    shot = req.shot or "Master Dramatic Scene Shot, 35mm film lens"
    sn = scene.get("scene_number", 1)
    
    out_dir = STORYBOARDS_DIR / f"scene_{sn:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "scene.png"
    
    try:
        # 1. Synthesize intelligent cinematic visual prompt
        image_prompt = build_cinematic_image_prompt(scene, shot)
        
        # 2. Call Stability AI
        success = generate_image(image_prompt, str(out_file))
        if not success or not out_file.exists():
            raise HTTPException(status_code=502, detail="Image generation failed. Check stability_image_error.log or API keys.")
            
        return {
            "success": True,
            "scene_number": sn,
            "image_url": f"/api/storyboards/scene_{sn:02d}/scene.png?t={int(time.time())}",
            "prompt": image_prompt,
            "shot": shot
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation error: {str(e)}")

@app.get("/api/storyboards/{path:path}")
def get_storyboard_image(path: str):
    file_path = STORYBOARDS_DIR / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Image not found")

@app.post("/api/clear")
def clear_all_workspace():
    try:
        if STORYBOARDS_DIR.exists():
            shutil.rmtree(STORYBOARDS_DIR, ignore_errors=True)
        STORYBOARDS_DIR.mkdir(parents=True, exist_ok=True)
        if BREAKDOWN_FILE.exists():
            os.remove(BREAKDOWN_FILE)
        return {"success": True, "message": "Workspace cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


FRONTEND_DIST = WORKSPACE_ROOT / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static_frontend")
