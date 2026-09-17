# DevNotes


## thoughts

Frontend:
- take in an uploaded photo or allow user to take a photo from their iOS or android phone

Backend:
- use that image to find out the similar food according to the shape, shade, color, patterns of image

Reference:
- here is a good past project can be used as example: 
https://github.com/jw4js/terriblehack17
(the backend was assuming everything is built on an android app, however, in this repo, we can research on if using react native or web page would be better off)

Research on:
- if we can leverage any models to do this similarity search (any open source libraries or techniques)
- maybe apis from black forest labs? google dalle? chatGPT image? any open source libraries


### Architecture overview

Proposed flow: `client captures/uploads photo -> backend API -> recognition service -> match/translate -> response with dish name, translation, description, confidence`

```
[Web/Mobile client] --(image)--> [API Gateway/BFF] --> [Recognition Service]
                                                            |-- Vision-LLM call (GPT-5 mini / Gemini Flash)
                                                            |-- CLIP embedding -> vector search (fallback/augment)
                                                            v
                                                     [Food metadata DB (Postgres)]
                                                     [Image blob storage (S3/GCS)]
```

- **Client**: takes/uploads a photo, sends to backend (never call third-party vision APIs directly from the client — keeps API keys server-side and lets us cache/rate-limit).
- **Backend/API**: thin service that stores the image, orchestrates recognition calls, applies caching (hash the image, skip re-calling paid APIs for duplicates), and returns a normalized response.
- **Recognition service**: hybrid approach (see below) — this is the core "translator" logic.
- **Metadata DB**: curated table of dishes with name, cuisine/region, common ingredients/allergens, and translations, keyed to embeddings for the vector-search path.
- **Storage**: uploaded photos in object storage with a retention/deletion policy (privacy — see below).

### Frontend

- **Decision: start with a responsive web app (PWA)**, not React Native, for v1.
  - `getUserMedia`/`<input capture>` covers photo capture and upload on both iOS Safari and Android Chrome without an app-store release cycle.
  - Ship a PWA manifest + service worker so it can be "installed" on iOS/Android home screens, narrowing the native-app gap for this use case (no background capture or advanced camera controls needed).
  - Revisit React Native later only if we need: offline-first behavior, push notifications, or deeper camera controls (manual focus/exposure) that the web camera API can't give us.
- Framework: React (Vite) to match likely team familiarity; keep it decoupled from backend so a native shell can wrap it later if needed.

### ML / recognition strategy

- **Decision: hybrid, LLM-vision-first with an embedding-based fallback**, rather than building a from-scratch classifier.
  - **Primary path — vision-capable LLM** (e.g. GPT-5 mini or Gemini Flash): send the photo with a prompt asking it to identify the dish, describe visible ingredients, and translate the name/description into the user's target language. This is the fastest path to a working product: zero training data, handles open-vocabulary/regional dishes reasonably well, and translation is a native capability (no separate translation API needed).
  - **Fallback/augment path — CLIP embeddings + vector similarity search**: for dishes the LLM gets wrong or is unsure about, and to build a growing proprietary dataset of user-corrected labels (regional/home-style dishes LLMs tend to miss). Store image embeddings + corrected metadata so repeat/similar photos resolve faster and cheaper without another LLM call.
  - Combine both with a confidence score; if the vector search returns a high-similarity curated match, prefer it (cheaper, and improves over time); otherwise fall back to the LLM call.
- Cache LLM responses by image hash to avoid re-paying for duplicate/near-duplicate uploads.
- Avoid AWS Rekognition Custom Labels / training a bespoke CNN for v1 — not worth the labeled-data and training-infra investment until we have real usage data to know where the LLM/CLIP hybrid actually falls short.

### Data storage

- **Metadata DB**: Postgres (dish name, region/cuisine, ingredients, allergens, translations).
- **Vector search**: start with `pgvector` inside the same Postgres instance (no new infra to run) rather than a dedicated vector DB; migrate to Qdrant only if/when vector volume or query latency demands it.
- **Image storage**: S3 (or GCS) with signed URLs and a retention policy — don't keep user photos indefinitely by default.

### Security & privacy

- Never expose third-party API keys (OpenAI/Google/AWS) to the client — all calls go through our backend.
- Food photos may contain incidental PII (people in the background, location metadata in EXIF) — strip EXIF on upload and set a default deletion window (e.g. 30 days) unless the user opts to save history.
- Rate-limit uploads per user/IP to control LLM API cost exposure and abuse.
- If self-hosting CLIP inference, keep the model server on a private network, not public-facing.

### Deployment

**Decision: split hosting** — GitHub Pages only serves static files, so it
can't run the FastAPI backend (needs to execute Python, hold
`OPENAI_API_KEY` server-side, make outbound OpenAI calls). The frontend and
backend deploy to two different hosts:

- **Frontend → GitHub Pages.** [`.github/workflows/deploy-frontend.yml`](.github/workflows/deploy-frontend.yml)
  builds `frontend/` on every push to `main` (or manual dispatch) and
  publishes `frontend/dist` via the official `actions/deploy-pages` action.
  [`frontend/vite.config.ts`](frontend/vite.config.ts) sets `base:
  '/food_translator/'` for production builds only (dev server stays at `/`),
  since a GitHub Pages project site is served at
  `https://<user>.github.io/<repo>/`, not the domain root.
- **Backend → Render.** [`render.yaml`](render.yaml) is a Render Blueprint
  describing the web service (root dir `backend`, build command
  `pip install -r requirements.txt`, start command `uvicorn app.main:app
  --host 0.0.0.0 --port $PORT`, and the env vars it needs).
  `OPENAI_API_KEY` is deliberately left out of the file (`sync: false`) —
  it's set as a secret directly in the Render dashboard, never committed.

**One-time setup steps** (do these once per environment, not per deploy):

1. Create a Render Blueprint from this GitHub repo — Render reads
   `render.yaml` and configures the service automatically.
2. In the Render dashboard, set the `OPENAI_API_KEY` secret (and optionally
   override `OPENAI_MODEL` / `OPENAI_IMAGE_MODEL` / `DAILY_REQUEST_CAP`).
   Note the resulting service URL, e.g. `https://foodify-backend.onrender.com`.
3. In the GitHub repo's Settings → Pages, set Source to "GitHub Actions".
4. In Settings → Secrets and variables → Actions → Variables, add a repo
   variable `VITE_API_URL` set to the Render URL from step 2 — this gets
   baked into the frontend build so it knows where to call.
5. Update `CORS_ORIGINS` in `render.yaml` (or the Render dashboard) to match
   the actual GitHub Pages origin, e.g. `["https://<user>.github.io"]`.

After that, every push to `main` redeploys both sides automatically —
`deploy-frontend.yml` on any `frontend/**` change, Render on any backend
change (via its own GitHub integration).

**Known gaps**: Render's free tier sleeps when idle (cold start on the first
request after a while) and has an ephemeral filesystem, so the local result
cache (`backend/.cache/`, see TODOs below) won't persist across Render
deploys/restarts the way it does on a local machine — every redeploy starts
with a cold cache there.

### Open questions

- [ ] Which target languages do we need to support at launch? (drives translation-quality testing)
- [ ] Do we need offline support (no connectivity while traveling) — if yes, revisit React Native + on-device model.
- [ ] Do we want user accounts/history, or fully anonymous/stateless per-photo lookups for v1?
- [ ] Seed dataset for the curated fallback — reuse Food-101 / Recipe1M, or start from the terriblehack17 reference repo's data?

### Public library / API tradeoff comparison

| Option | Category | Pricing (as of Sep 2026) | Functional fit | Maintenance burden | Security/privacy |
|---|---|---|---|---|---|
| **GPT-5 mini / GPT-5.6 (OpenAI)** vision | Vision-LLM API | Token-based; mini tier priced well below flagship (flagship GPT-5.6 Sol ~$5/$30 per 1M in/out tokens; mini tiers substantially cheaper) | Strong: open-vocabulary dish ID + built-in translation + description in one call. Best fit for "translator" framing. | Low — no infra, just an API call; but locked into OpenAI's roadmap/pricing changes | Images sent to OpenAI; check data-retention/opt-out settings; no on-prem option |
| **Gemini 2.5/3.x Flash (Google)** vision | Vision-LLM API | ~$0.30/$2.50 per 1M in/out tokens (Flash tier) — cheaper than GPT for high volume | Comparable to GPT for dish ID + translation; strong multilingual support (Google's translation heritage) | Low — API call only | Images sent to Google Cloud; same third-party data-handling tradeoff as OpenAI |
| **Google Cloud Vision API** (label/web detection) | Managed CV API | $1.50/1,000 units (label/OCR/face/logo), $3.50/1,000 (web detection); first 1,000/month free | Weak alone: generic label detection, not dish-specific or translation-aware. Would need to pair with a translation API. | Low, but need to build the "food-specific" logic ourselves on top | Images sent to Google; mature enterprise compliance posture (SOC2/HIPAA options) |
| **AWS Rekognition (+ Custom Labels)** | Managed CV API | Base detection cheap per image; Custom Labels training ~$1/hr, inference ~$4/hr | Generic recognition out of the box is not food-specific; Custom Labels could work but needs a labeled dataset and ongoing retraining as menu of dishes grows | High — custom model lifecycle (labeling, retraining, versioning) is on us | Images sent to AWS; strong enterprise compliance (SOC2/HIPAA), data stays in our AWS account/region |
| **Clarifai food-item-recognition model** | Hosted food-specific model | Usage-based (per-call credits); has a free tier | Food-specific (740 tags) but measured accuracy is mediocre (~38% top-1 in independent comparisons) and no built-in translation | Low (hosted), but accuracy ceiling means we'd still need a fallback | Images sent to Clarifai; smaller vendor, less compliance tooling than AWS/Google |
| **LogMeal API** | Hosted food-specific API | Subscription + per-call credits (tiered plans) | Food-specific, recognizes 1,300+ dishes, includes nutrition/portion estimation — closest off-the-shelf fit to our use case, but no translation and coverage skews toward common/Western dishes | Low (hosted), vendor lock-in for a niche provider (smaller company, roadmap risk) | Images sent to a smaller third party; verify their data retention/DPA before using with user photos |
| **CLIP (open source, self-hosted) + FAISS/pgvector** | Open-source embedding model + vector search | Free (model + library); pay only for compute to run inference (GPU optional, CPU works for small scale) and storage | Not a classifier out of the box — needs us to curate a labeled reference image set to match against, and doesn't translate on its own. Best as the "fallback/learn over time" layer, not primary. | Highest — we own model updates, embedding pipeline, curation of the reference dataset, and infra | Best privacy option: can run fully self-hosted, no image leaves our infra |
| **pgvector** (vector search in Postgres) | Vector DB (embedded) | Free, part of existing Postgres | Sufficient for our expected scale (curated dish dataset, not billions of vectors) | Low — no new service to operate | Data stays in our existing DB/infra |
| **Qdrant / Milvus / Weaviate / Pinecone** | Dedicated vector DB | Qdrant: free self-hosted or 1GB free managed tier, cheapest at scale; Pinecone: managed, free tier then usage-based; Weaviate: free trial then paid; Milvus: free self-hosted, built for 100M+ vectors | Overkill for v1 scale; worth revisiting if the curated reference dataset grows past what pgvector handles well | Qdrant (self-hosted) and Milvus need ops (Docker/K8s); Pinecone is zero-ops but adds a vendor | Pinecone/Weaviate managed = data leaves our infra; Qdrant/Milvus can be self-hosted for full control |

**Recommendation**: launch with a vision-LLM (GPT-5 mini or Gemini Flash, pick based on final pricing/translation-quality bake-off) as the primary recognition+translation path, backed by `pgvector` for a growing curated fallback dataset — avoids standing up dedicated ML infra or a vector DB service before we have real usage data to justify it.


### TODOs

- [x] make sure we don't expose the api keys — `.env` files are gitignored in both `backend/` and `frontend/` and nothing is tracked in git; the frontend only ever calls our own backend, never OpenAI directly.
- [x] control and monitor the image api billing budget — `/api/identify` (`backend/app/main.py`) now (1) caches responses by image hash to a local JSON file (`backend/.cache/`), so a duplicate/repeat photo upload skips both the recognition and image-generation OpenAI calls entirely and survives process restarts, and (2) enforces a `DAILY_REQUEST_CAP` (default 10) on calls that actually hit OpenAI — cache hits don't count against it. The daily counter is still in-memory (resets on restart) and neither has a size cap — fine for local dev, but revisit with a real store/hard spend cap before this handles real multi-user traffic. Note Render's filesystem is ephemeral, so the disk cache won't survive deploys/restarts there.
- [ ] display the chain of thoughts while fetching api results
- [x] add deployment instructions — see the [Deployment](#deployment) section above for the setup steps and rationale, and [README.md#deployment](README.md#deployment) for the quick version.

