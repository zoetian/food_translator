# Food Translator

Take a photo of anything and find the food it most resembles — name, description, and a translation into your language.

See [DevNotes.md](DevNotes.md) for architecture and design decisions.

## Running locally

### Backend (FastAPI)

```
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # then fill in OPENAI_API_KEY
.venv/bin/uvicorn app.main:app --reload --port 8000
```

### Frontend (React + Vite)

```
cd frontend
npm install
cp .env.example .env   # defaults to http://localhost:8000
npm run dev
```

Then open http://localhost:5173.
