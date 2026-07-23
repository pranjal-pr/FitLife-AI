# FitLife - AI Fitness and Nutrition Coach

<div align="center">

**Scan food labels, review workout form, and ask FitLife Coach for meal and recovery guidance.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com)
[![Tailwind](https://img.shields.io/badge/Tailwind_CSS-4.0-38bdf8)](https://tailwindcss.com)

</div>

---

## Maintained Version

This repository is maintained by [pranjal-pr](https://github.com/pranjal-pr) and is configured for an independent deployment. It is based on the original [FitLife-AI project](https://github.com/shinzoxD/FitLife-AI) by Nishchay Sharma (`shinzoxD`). See [License](#license) for reuse terms and attribution.

Deployment URLs are intentionally supplied through environment variables instead of pointing at the upstream author's services.

---

## Overview

FitLife is a full-stack fitness product with three core surfaces:

- **Fuel Scan** - upload a nutrition label photo and get extracted nutrition data, scoring, and profile-aware recommendations.
- **Form Coach** - upload a workout clip and receive rep counting, movement scoring, and coaching cues powered by YOLO pose checkpoints.
- **FitLife Coach** - ask nutrition and recovery questions through a profile-aware AI assistant.

The zero-cost deployment architecture uses:

- `Hugging Face Static Spaces` for the exported Next.js frontend
- `Render` for the lightweight Flask backend

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React 19, Tailwind CSS 4, TypeScript |
| Backend API | Flask, SQLAlchemy, PyJWT, Flask-Login |
| AI / ML | YOLOv8 pose, Groq vision/text models, RAG retrieval |
| Async Tasks | Celery + Redis (optional) |
| Database | SQLite (dev), PostgreSQL / Neon (prod) |
| Deployment | Hugging Face Static Spaces (frontend) + Render (backend) |

---

## Project Structure

```text
fitlife/
|-- frontend/                # Next.js frontend
|-- gateway/                 # Flask API gateway
|-- services/
|   |-- muscle_ai_service/   # Workout analysis service
|   |-- nutri_ai_service/    # Nutrition / RAG service
|   `-- shared/database/     # Shared SQLAlchemy models
|-- data/
|   `-- nutri-ai/            # Knowledge base JSON files
|-- model/
|   `-- models/              # Tracked YOLO workout checkpoints
|-- docs/                    # Resume + deployment docs
`-- web/                     # Legacy Jinja templates / static output
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Groq API key for nutrition OCR / chat features

### 1. Clone the repo

```bash
git clone https://github.com/pranjal-pr/FitLife-AI.git
cd FitLife-AI
```

### 2. Backend setup

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy env.example .env
```

Edit `.env` and set at least:

- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `GROQ_API_KEY`
- `DATABASE_URL` for PostgreSQL in production

### 3. Frontend setup

```bash
cd frontend
npm install
copy .env.example .env.local
cd ..
```

Set this in `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:5000
```

### 4. Run locally

Open two terminals:

```bash
# Terminal 1
python gateway/app.py

# Terminal 2
cd frontend && npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Workout Models

The workout checkpoints are tracked in:

- `model/models`

Current checkpoints:

- `best.pt`
- `sumo_best.pt`
- `squats_best.pt`
- `best_romanian.pt`
- `zercher_best.pt`
- `front_squats_best.pt`

The workout service auto-resolves these from:

- `services/muscle_ai_service/config/settings.py`

To inspect embedded validation metrics:

```bash
G:\fitlife\.venv\Scripts\python.exe scripts\evaluate_muscle_models.py
```

To run a fresh validation pass once you have the dataset YAML:

```bash
G:\fitlife\.venv\Scripts\python.exe scripts\evaluate_muscle_models.py --data path\to\config.yaml
```

---

## API Endpoints

All API routes are prefixed with `/api/v1/`.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | - | Create account |
| POST | `/auth/login` | - | Get JWT tokens |
| POST | `/auth/refresh` | - | Refresh access token |
| GET | `/user` | JWT | Get user profile |
| PUT | `/user/settings` | JWT | Update profile |
| GET | `/user/scans` | JWT | Scan history |
| GET | `/user/workouts` | JWT | Workout history |
| GET | `/dashboard/stats` | JWT | Dashboard statistics |
| POST | `/nutri-ai/upload` | Optional | Upload nutrition label |
| POST | `/nutri-ai/analyze` | Optional | Analyze extracted nutrition data |
| POST | `/muscle-ai/upload` | Optional | Upload workout video |
| GET | `/muscle-ai/task/:id` | - | Poll async task status |
| POST | `/ana/chat` | Optional | Chat with FitLife Coach |

---

## Environment Variables

Use [`env.example`](env.example) as the base. The important ones are:

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Flask session secret |
| `JWT_SECRET_KEY` | Yes | JWT signing secret |
| `DATABASE_URL` | Production | PostgreSQL connection string (Neon works well) |
| `GROQ_API_KEY` | For nutrition/chat | Groq API key |
| `FRONTEND_URL` | In production | Public Vercel frontend URL |
| `NEXT_PUBLIC_API_URL` | Frontend | Public backend URL |

---

## Deployment

### Zero-cost deployment: Hugging Face Static Space + Render

#### 1. Deploy the backend on Render

- Create a Render Blueprint from this GitHub repository.
- Render reads the root [`render.yaml`](render.yaml) and creates
  `fitlife-ai-api` on the free plan.
- Set `GROQ_API_KEY` for nutrition scanning and chat.
- Set `FRONTEND_URL=https://praanjalpradhan-fitlife-ai.hf.space`.
- `SECRET_KEY` and `JWT_SECRET_KEY` are generated by the Blueprint.
- `DATABASE_URL` and Google OAuth variables are optional.

Copy the resulting URL, such as
`https://fitlife-ai-api.onrender.com`.

#### 2. Connect GitHub Actions

Add these GitHub repository secrets:

- `HF_TOKEN`
- `HF_SPACE_REPO=praanjalpradhan/fitlife-ai`
- `NEXT_PUBLIC_API_URL=https://fitlife-ai-api.onrender.com`

The Hugging Face job builds the frontend with `STATIC_EXPORT=true`, copies the
metadata from
[`docs/HUGGINGFACE_STATIC_README.md`](docs/HUGGINGFACE_STATIC_README.md), and
pushes the generated site to the Static Space.

#### 3. Deploy

Run the `CD` workflow manually after the Render backend is healthy. The public
frontend will be available at:

`https://praanjalpradhan-fitlife-ai.hf.space`

Notes:

- Render free services sleep after inactivity, so the first API request can
  take approximately one minute.
- Free Render storage is ephemeral. Use an external PostgreSQL database for
  durable accounts and history.
- Nutrition scanning and chat use the lightweight gateway. Local YOLO video
  analysis may exceed the memory available on a free Render instance.

---

## GitHub Actions CI/CD

This repo now includes:

- [`ci.yml`](.github/workflows/ci.yml) for frontend build, gateway smoke tests, and workout model loading
- [`cd.yml`](.github/workflows/cd.yml) for production deployment from `main`

### Required GitHub Secrets

For the Vercel deployment job:

- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

For the Hugging Face Space deployment job:

- `HF_TOKEN`
- `HF_SPACE_REPO`
- `NEXT_PUBLIC_API_URL`

Example `HF_SPACE_REPO` value:

```text
your-hugging-face-user/fitlife-ai
```

### How the pipeline works

- Pull requests and pushes run `CI`
- A successful `CI` run on `main` triggers `CD`
- `CD` deploys the frontend to Vercel when Vercel secrets are present
- `CD` exports and syncs the frontend to your Hugging Face Static Space

If you use the GitHub Actions Vercel deploy, disable duplicate auto-deploy behavior in Vercel if you do not want both Git integration and Actions creating separate production deployments.

---

## Resume Positioning

Use [`docs/RESUME_PROJECT.md`](docs/RESUME_PROJECT.md) for resume bullets, a portfolio summary, and interview talking points.

---

## Acknowledgments

- Ultralytics YOLOv8 for pose estimation
- Groq for nutrition OCR and text inference
- Harvard Medical School nutrition research used in the knowledge base
- Nishchay Sharma (`shinzoxD`) for the original FitLife-AI project and commit history

---

## License

This project is licensed under the [MIT License](LICENSE). The original copyright and license notice are retained as required by that license.
