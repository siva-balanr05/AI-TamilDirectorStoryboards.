# 🎬 AI Director

An intelligent film pre-production assistant that transforms raw scripts into structured scene breakdowns and AI-generated storyboards. Supports Tamil and multilingual scripts with automated shot analysis powered by Google Gemini and Stability AI.

---

## ✨ Features

- **📄 Script Ingestion** — Upload scripts as `.txt`, `.pdf`, or `.docx` files
- **🧠 AI Scene Breakdown** — Automatically extracts scenes, characters, props, locations, time-of-day, audio cues, and action lines
- **🎞️ Shot List Generation** — Produces professional shot lists with camera types (Close-up, Wide Shot, OTS, etc.), angles, and movement
- **🖼️ Storyboard Generation** — Generates visual storyboard frames using Stable Diffusion XL via the Stability AI API
- **🌐 Multilingual Support** — Native support for Tamil scripts; extensible to other Indian and world languages
- **📦 Dataset Export** — Exports structured JSON datasets for downstream ML training and fine-tuning
- **🔄 Retry & Rate Limiting** — Exponential backoff with jitter for robust API handling across Gemini model tiers
- **🗂️ Workspace Management** — Auto-cleans stale session data on startup; supports one-click workspace reset

---

## 🗂️ Project Structure

```
aidirector/
├── Projects/
│   └── ai-director/
│       ├── app1.py                    # Main Streamlit application
│       ├── app_new.py                 # Experimental updated UI
│       ├── requirements.txt           # Python dependencies
│       ├── script.txt                 # Sample script file
│       ├── src/
│       │   ├── model_utils.py         # Gemini & Stability AI API wrappers
│       │   ├── language_utils.py      # Multilingual prompt templates
│       │   ├── dataset_converter.py   # Script → structured dataset converter
│       │   ├── dataset_converter_new.py
│       │   └── storyboard_generator.py
│       └── storyboards/               # Output: generated storyboard images
├── script_datasets/                   # Sample script analysis JSON datasets
│   └── a_few_good_men/
│       ├── script_analysis.json
│       ├── shot_analysis.json
│       └── image_generation.json
├── storyboards/                       # Root-level storyboard outputs
│   ├── scene_01/
│   └── scene_02/
└── script_breakdown.json              # Sample Tamil script breakdown output
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A [Google Gemini API Key](https://aistudio.google.com/app/apikey)
- A [Stability AI API Key](https://platform.stability.ai/) *(for image generation)*

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/siva-balanr05/aidir.git
cd aidir/Projects/ai-director

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file inside `Projects/ai-director/` with your API keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
STABILITY_API_KEY=your_stability_ai_api_key_here
```

> **Note:** `.env` is git-ignored. Never commit your API keys.

### Running the App

```bash
cd Projects/ai-director
streamlit run app1.py
```

The app will open at `http://localhost:8501`.

---

## 🧩 How It Works

```
Script File (txt/pdf/docx)
        │
        ▼
  Language Detection & Parsing
        │
        ▼
  Gemini AI — Scene Breakdown
  (location, time, characters, props, dialogues, action)
        │
        ▼
  Gemini AI — Shot List Generation
  (shot type, angle, movement, dialogue mapping)
        │
        ▼
  Stability AI SDXL — Storyboard Frame Generation
        │
        ▼
  Streamlit UI — Visual Storyboard + JSON Export
```

---

## 🤖 AI Models Used

| Purpose              | Model / API                          |
|----------------------|--------------------------------------|
| Script analysis      | `gemini-2.5-flash` (with fallback chain) |
| Shot list generation | `gemini-2.0-flash-lite`, `gemini-2.0-flash` |
| Storyboard images    | Stability AI — `stable-diffusion-xl-1024-v1-0` |

The Gemini integration uses a **multi-tier fallback chain** — if one model hits its daily quota, the next model in the list is tried automatically.

---

## 🌐 Language Support

| Language | Status          |
|----------|-----------------|
| Tamil (தமிழ்)   | ✅ Full support |
| English  | ✅ Full support |
| Hindi    | 🔄 Extensible   |
| Others   | 🔄 Extensible   |

Language-specific prompt templates are defined in [`src/language_utils.py`](Projects/ai-director/src/language_utils.py). Adding a new language only requires adding an entry to `SUPPORTED_LANGUAGES`.

---

## 📊 Sample Output

The `script_breakdown.json` at the root contains a sample breakdown of a Tamil thriller script *"கடைசி தீர்மானம்"* (The Final Decision) — demonstrating the structured JSON output with scenes, dialogues, and shot recommendations.

```json
{
  "title": "கடைசி தீர்மானம்",
  "scenes": [
    {
      "scene_number": 1,
      "location": "காவல் நிலையம்",
      "time": "இரவு",
      "characters": ["கார்த்திக்", "ரகுநாத்"],
      "dialogues": [
        {
          "character": "கார்த்திக்",
          "line": "மூன்று வருஷமா தேடுறோம். இன்னைக்கு கட்டாயம் பதில் சொல்லணும்.",
          "shots": [
            "Medium Shot - Inspector Karthik opening the case file with a tired expression.",
            "Close-up - Karthik's weary face as he delivers the line."
          ]
        }
      ]
    }
  ]
}
```

---

## 📦 Dependencies

| Package            | Purpose                               |
|--------------------|---------------------------------------|
| `streamlit`        | Web UI framework                      |
| `google-generativeai` | Gemini API client                  |
| `requests`         | Stability AI HTTP calls               |
| `python-dotenv`    | Environment variable management       |
| `docx2txt`         | Word document parsing                 |
| `PyPDF2`           | PDF script parsing                    |
| `Pillow`           | Image processing                      |
| `torch` + `transformers` | Local model support (optional)  |

---

## 🔒 Security

- API keys are loaded exclusively from `.env` via `python-dotenv`
- `.env` is listed in `.gitignore` — never committed
- The `storyboards/` output directory is also git-ignored

---

## 🛠️ Development

```bash
# Run with hot-reload
streamlit run app1.py --server.runOnSave true

# Lint
pip install ruff
ruff check src/
```

---

## 📄 License

This project is currently unlicensed. All rights reserved by the author.

---

## 🙏 Acknowledgements

- [Google Gemini](https://deepmind.google/technologies/gemini/) for multilingual AI reasoning
- [Stability AI](https://stability.ai/) for SDXL image generation
- [Streamlit](https://streamlit.io/) for the rapid UI framework
