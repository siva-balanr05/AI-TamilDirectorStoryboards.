# 🎬 AI Director Pro • Studio 2.5

An intelligent cinematic pre-production suite and screenplay deconstruction studio that transforms raw movie scripts into structured scene breakdowns, director camera shot lists, and photorealistic AI-generated storyboards. Supports **Tamil**, **English**, **Hindi**, and **Telugu** screenplays.

Powered by **Google Gemini** (for screenplay analysis & visual prompt synthesis) and **Stability AI SDXL** (for 16:9 cinematic storyboard frames).

---

## ✨ Features

- **🎞️ Hollywood NLE Production Studio (React 19 + Tailwind CSS + Vite)**:
  - **🎬 Viewfinder Monitor Mode**: Real-time camera viewfinder monitor with corner bracket markings, center crosshairs, Rule-of-Thirds grid overlay, and live SMPTE timecode (24 FPS).
  - **🖼️ Storyboard Deck Mode**: Wall-of-frames visual gallery to preview, generate, and review storyboards for all scenes side-by-side.
  - **📜 Script Teleprompter Mode**: Industry-standard monospace screenplay reader for rehearsals.
  - **🎨 4 Studio Themes**: *Midnight Cinema* (Gold/Amber), *Cyber Neo-Noir* (Cyan/Emerald), *Hollywood 35mm* (Crimson/Red), and *Director Titanium* (Monochrome Silver).
- **⚡ High-Performance FastAPI Backend**:
  - Script ingestion from `.txt`, `.pdf`, and `.docx` files.
  - Scene breakdown extraction: locations, time of day, weather, characters, props, audio cues, sequential action beats, and dialogues.
  - AI Cinematographer Prompt Synthesizer (`build_cinematic_image_prompt`) that converts cultural/dramatic nuances into rich English diffusion prompts.
- **🎥 Shot Framing & Cinematography Presets**:
  - Close-up, Extreme Close-up, Medium Two-Shot, Wide Establishing Shot, Low Angle, Dutch Angle, Over-the-Shoulder.
- **🖼️ 16:9 Widescreen Storyboard Generation**:
  - High-resolution rendering (`1344x768`) via Stable Diffusion XL (`stable-diffusion-xl-1024-v1-0`).
  - Fullscreen lightbox mode and one-click frame downloads.
  - Transparent AI prompt inspector showing the exact synthesized English visual prompt.
- **🎬 Streamlit Fallback Dashboard**:
  - Includes `app_new.py` for rapid local prototyping in Streamlit.

---

## 🗂️ Project Structure

```
AI-TamilDirectorStoryboards/
├── backend/
│   └── server.py                      # FastAPI REST API & static server
├── frontend/                          # React 19 + Vite + Tailwind CSS Studio
│   ├── src/
│   │   ├── App.jsx                    # Hollywood NLE Director Studio UI
│   │   ├── index.css                  # Custom cinematic dark styling & glows
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js                 # API proxy to localhost:8000
├── src/
│   ├── model_utils.py                 # Gemini LLM fallback chain & SDXL generator
│   ├── language_utils.py              # Multilingual directorial prompts (Tamil/EN/HI/TE)
│   ├── dataset_converter.py           # Movie script → ML training dataset converter
│   └── storyboard_generator.py        # Image generator abstraction
├── app_new.py                         # Streamlit multi-language web app
├── app1.py                            # Streamlit prototype
├── requirements.txt                   # Python dependencies
├── script.txt                         # Sample Tamil screenplay test file
└── script_breakdown.json              # Latest structured scene breakdown output
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** & **npm**
- [Google Gemini API Key](https://aistudio.google.com/app/apikey)
- [Stability AI API Key](https://platform.stability.ai/)

---

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/siva-balanr05/AI-TamilDirectorStoryboards..git
cd AI-TamilDirectorStoryboards.

# Setup Python Virtual Environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

---

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
STABILITY_API_KEY=your_stability_ai_key_here
```

> **Note:** `.env` is git-ignored for security. Never commit API keys.

---

### 3. Running the Studio

#### Option A: React Studio + FastAPI (Recommended)

1. **Start the FastAPI Backend:**
   ```bash
   uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
   ```
2. **Start the React Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```
3. Open **[http://localhost:5173](http://localhost:5173)** in your browser!

#### Option B: Streamlit Dashboard

```bash
streamlit run app_new.py
```
Opens at **[http://localhost:8501](http://localhost:8501)**.

---

## 🧩 Workflow Architecture

```
Raw Script (Tamil/English/Hindi/Telugu or PDF/DOCX)
                    │
                    ▼
          [LanguageManager Engine]
                    │
                    ▼
         [Gemini LLM Breakdown]
  Locations • Time • Weather • Characters • Props • Actions • Dialogues
                    │
                    ▼
    [Cinematographer Prompt Synthesizer]
  Translates dramatic action + dialogue emotion into visual English cues
                    │
                    ▼
      [Stability AI SDXL Rendering]
  16:9 Widescreen Storyboard Frame (1344x768)
                    │
                    ▼
    [React Viewfinder / Storyboard Deck]
```

---

## 📄 License

MIT License. Created for filmmakers, directors, and AI cinema storytellers.
