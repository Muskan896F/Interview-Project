# Shubh Residency - AI Outbound Real Estate Voice Agent

A production-quality outbound voice agent simulation built with **FastAPI**, **LangGraph**, and **Pydantic** to qualify leads and schedule site visits for *Shubh Residency* in Shela, Ahmedabad.

---

## Core Capabilities
- **Stateful Workflows**: Built on LangGraph `StateGraph` supporting condition-based dialogue routing (Greeting, Qualification, Objections, Knowledge, Booking, Summary).
- **Code-Mixed Languages**: Primarily speaks Gujarati naturally mixed with English keywords (and dynamically shifts to Hindi/English when the client switches).
- **Voice Conversions**: Integrated with Deepgram STT API for audio speech transcription, and Sarvam Bulbul API for high quality Gujarati text-to-speech generation.
- **Mock Fallback Engine**: Runs in full rule-based simulation out-of-the-box if external API subscription keys are not configured.

---

## Folder Structure
```
real-estate-voice-agent/
│
├── main.py                     # FastAPI server entry point
├── requirements.txt            # Python package dependencies
├── .env.example                # Environment variables template (committed to Git)
├── .env                        # Active Environment keys (ignored by Git)
├── .gitignore
├── README.md
│
├── app/
│   ├── api/                    # REST routers & schema models
│   ├── graph/                  # LangGraph nodes & state workflow
│   ├── services/               # Generative LLM & Speech API drivers
│   ├── database/               # SQLite ORM models & CRUD interfaces
│   ├── config/                 # Pydantic-settings & constants
│   ├── knowledge/              # JSON facts knowledge bases
│   └── prompts/                # Raw dialogue text templates
│
├── frontend/                   # HTML/CSS/JS web dashboard
├── docs/                       # Architectural design files
└── tests/                      # Python automated test suite
```

---

## Detailed Local Setup & Execution Guide

Follow these step-by-step instructions to get the application running locally on your system.

### Prerequisites
- **Python 3.9+** installed on your system.
- (Optional) API keys for LLM (OpenAI), Deepgram, and Sarvam. If no keys are provided, the system automatically falls back to **Mock Simulation Mode** for testing.

---

### Step 1: Open Terminal & Navigate to Project Directory
Navigate to the root directory where the codebase is located:
```bash
cd real-estate-voice-agent
```

---

### Step 2: Set up a Virtual Environment
Isolate python dependencies using a virtual environment:

* **On Windows (Command Prompt / CMD):**
  ```cmd
  python -m venv .venv
  .venv\Scripts\activate
  ```

* **On Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\activate
  ```
  *(Note: If you get a script execution policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` first)*

* **On macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

---

### Step 3: Install Required Dependencies
Upgrade pip and install python packages listed in `requirements.txt`:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 4: Configure Environment Variables (`.env`)
The repository contains a template file called `.env.example` which is committed to Git. You need to create a `.env` file from it:

1. **Copy the example template:**
   * **On Windows (CMD/PowerShell):**
     ```bash
     copy .env.example .env
     ```
   * **On macOS / Linux:**
     ```bash
     cp .env.example .env
     ```

2. **Configure your API keys:**
   - **LLM_PROVIDER**: Set to `openai`.
   - **OPENAI_API_KEY**: Provide your OpenAI API key.
   - **DEEPGRAM_API_KEY**: Deepgram subscription API key for Speech-to-Text transcription.
   - **SARVAM_API_KEY**: Sarvam AI API key for Bulbul (Gujarati) Text-to-Speech audio generation.
   
   *Note: If these keys are left as placeholder text or empty, the app will run in **Mock Simulation Mode** automatically.*

---

### Step 5: Run the Server
Start the backend FastAPI server:
```bash
python main.py
```
Or run it directly using Uvicorn:
```bash
uvicorn main:app --reload
```

During startup:
- The app will automatically initialize the local SQLite database schema.
- A local SQLite database file `leads.db` will be created inside the `data/` directory.

---

### Step 6: Access the Frontend Dashboard
Once the server is running successfully, open your browser and navigate to:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

From the dashboard, you can:
- View current lead qualifications.
- Trigger outbound dial simulations.
- Interact with the voice bot (in Mock or Real voice mode).

---

## Running Automated Tests

To run the unit/integration tests and verify the code-level logic:
```bash
python -m unittest discover tests
```
Or run:
```bash
pytest
```
