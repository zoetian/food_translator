# Foodify

Point a photo at anything — food, an animal, an object, a cartoon character — and Foodify finds the food it most visually resembles, then generates a picture of that imagined dish.

See [DevNotes.md](DevNotes.md) for architecture and design decisions.

## How it works

1. You upload or snap a photo.
2. A vision-capable LLM (GPT-5 mini by default, via OpenAI's Responses API) looks at the shape, color, texture, and pattern of the subject and invents the food it most resembles — it's not literal dish identification.
3. OpenAI's image API generates a picture of that imagined food.

💰 **Cost controls**: step 3 makes a paid image-generation call, so the backend caches results by photo hash (duplicate uploads are free) and caps calls that actually hit OpenAI at `DAILY_REQUEST_CAP` per day (default 10, see `.env.example`). Both live in memory only and reset on restart — fine for local dev, not yet built for real multi-user traffic (tracked in [DevNotes.md](DevNotes.md#todos)).

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
