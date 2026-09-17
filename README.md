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

### Backend → Google Cloud Run

Cloud Run's free tier (~2M requests/month, scales to zero when idle) is a
better fit for a low-traffic personal project than Render's paid-only
"always on" plans. One-time setup in the [Google Cloud Console](https://console.cloud.google.com):

1. Create (or pick) a GCP project and enable the **Cloud Run**, **Cloud
   Build**, and **Artifact Registry** APIs for it.
2. Create a service account with the **Cloud Run Admin**, **Cloud Build
   Editor**, **Artifact Registry Writer**, and **Service Account User** roles.
   Generate a JSON key for it.
3. In this GitHub repo, Settings → Secrets and variables → Actions → **Secrets**,
   add:
   - `GCP_SA_KEY` — the full JSON key content from step 2.
   - `GCP_PROJECT_ID` — your GCP project ID.
   - `OPENAI_API_KEY` — your real OpenAI key (never committed to the repo).
4. Push to `main` (or run manually from the Actions tab) —
   [`.github/workflows/deploy-backend.yml`](.github/workflows/deploy-backend.yml)
   builds [`backend/Dockerfile`](backend/Dockerfile) and deploys it to Cloud
   Run as the `foodify-backend` service in `us-central1`.
5. After the first deploy, note the service URL Cloud Run prints, e.g.
   `https://foodify-backend-xxxxx.us-central1.run.app`.

If your GitHub Pages URL isn't `https://<your-github-username>.github.io`,
update the `CORS_ORIGINS` value inside
[`.github/workflows/deploy-backend.yml`](.github/workflows/deploy-backend.yml)
to match.

Cloud Run still cold-starts after idle (same tradeoff as any scale-to-zero
host), and its filesystem is ephemeral, so the local result cache
(`backend/.cache/`) won't persist across deploys/restarts there the way it
does locally.

### Frontend → GitHub Pages

1. In the repo's Settings → Pages, set Source to "GitHub Actions".
2. In Settings → Secrets and variables → Actions → Variables, add a repo
   variable `VITE_API_URL` set to your deployed Cloud Run URL (step 5 above).
3. Push to `main` (or run the workflow manually from the Actions tab) —
   [`.github/workflows/deploy-frontend.yml`](.github/workflows/deploy-frontend.yml)
   builds `frontend/` and publishes it to Pages.
4. The site will be live at `https://<your-github-username>.github.io/food_translator/`.

If you rename or fork the repo, update the hardcoded `/food_translator/` base
path in [`frontend/vite.config.ts`](frontend/vite.config.ts) to match.
