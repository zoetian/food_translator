# Foodify

Point a photo at anything — food, an animal, an object, a cartoon character — and Foodify finds the food it most visually resembles, then generates a picture of that imagined dish.

See [DevNotes.md](DevNotes.md) for architecture and design decisions.

## How it works

1. You upload or snap a photo.
2. A vision-capable LLM (GPT-5 mini by default, via OpenAI's Responses API) looks at the shape, color, texture, and pattern of the subject and invents the food it most resembles — it's not literal dish identification.
3. OpenAI's image API generates a picture of that imagined food.

💰 **Cost controls**: step 3 makes a paid image-generation call, so the backend caches results by photo hash (duplicate uploads are free, cached to `backend/.cache/` so it survives restarts) and caps calls that actually hit OpenAI at `DAILY_REQUEST_CAP` per day (default 10, see `.env.example`; this counter is in-memory and resets on restart). Fine for local dev, not yet built for real multi-user traffic (tracked in [DevNotes.md](DevNotes.md#todos)).

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

## Deployment

GitHub Pages only serves static files, so it can host the frontend but not the
FastAPI backend. The two deploy separately:

### Backend → Render

1. Push this repo to GitHub, then create a new [Render](https://render.com) Blueprint
   from it — Render reads [`render.yaml`](render.yaml) and configures the
   service automatically (root dir `backend`, build/start commands, env vars).
2. In the Render dashboard, set the `OPENAI_API_KEY` secret (left out of
   `render.yaml` on purpose — never commit real keys). Adjust `OPENAI_MODEL`,
   `OPENAI_IMAGE_MODEL`, or `DAILY_REQUEST_CAP` there too if you want different
   defaults.
3. Once deployed, note the service URL, e.g. `https://foodify-backend.onrender.com`.
4. Update `CORS_ORIGINS` in `render.yaml` (or directly in the Render dashboard)
   to match your actual GitHub Pages URL if it differs from
   `https://<your-github-username>.github.io`.

Render's free tier spins down when idle, so the first request after a while
will be slow (cold start) — and its filesystem is ephemeral, so the local
result cache (`backend/.cache/`) won't persist across deploys/restarts there
the way it does locally.

### Frontend → GitHub Pages

1. In the repo's Settings → Pages, set Source to "GitHub Actions".
2. In Settings → Secrets and variables → Actions → Variables, add a repo
   variable `VITE_API_URL` set to your deployed Render backend URL (step 3
   above).
3. Push to `main` (or run the workflow manually from the Actions tab) —
   [`.github/workflows/deploy-frontend.yml`](.github/workflows/deploy-frontend.yml)
   builds `frontend/` and publishes it to Pages.
4. The site will be live at `https://<your-github-username>.github.io/food_translator/`.

If you rename or fork the repo, update the hardcoded `/food_translator/` base
path in [`frontend/vite.config.ts`](frontend/vite.config.ts) to match.
