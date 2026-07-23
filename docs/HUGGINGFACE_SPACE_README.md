---
title: AI Fit Pro API
emoji: "💪"
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: AI fitness and nutrition backend API
---

# AI Fit Pro API

This Space runs the Flask backend for AI Fit Pro and is maintained by
[pranjal-pr](https://github.com/pranjal-pr).

It is based on the original
[FitLife-AI project](https://github.com/shinzoxD/FitLife-AI) by Nishchay
Sharma (`shinzoxD`) and retains the project's MIT license notice.

Set these Space variables before the first launch:

- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `GROQ_API_KEY`
- `FRONTEND_URL`
- `GOOGLE_CLIENT_ID` (optional)
- `GOOGLE_CLIENT_SECRET` (optional)

The backend serves:

- `/health`
- `/api/v1/health`
- `/api/v1/nutri-ai/*`
- `/api/v1/muscle-ai/*`
- `/api/v1/ana/chat`

See [`LICENSE`](LICENSE) for reuse terms and attribution.
