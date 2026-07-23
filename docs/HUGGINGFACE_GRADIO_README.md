---
title: FitLife AI
emoji: 💪
colorFrom: orange
colorTo: green
sdk: gradio
sdk_version: 6.20.0
python_version: 3.10.13
app_file: app.py
pinned: false
license: mit
short_description: Nutrition scanning, workout analysis, and AI coaching
---

# FitLife AI

FitLife AI is a Gradio demo for:

- profile-aware nutrition-label analysis;
- YOLO-powered workout form analysis; and
- nutrition and recovery chat.

Set `GROQ_API_KEY` in the Space **Settings → Secrets** page to enable nutrition
OCR, scoring, and AI chat. Workout analysis uses the model checkpoints bundled
with this Space.

This Space is maintained by
[pranjal-pr](https://github.com/pranjal-pr/FitLife-AI). It is based on the
original [FitLife-AI project](https://github.com/shinzoxD/FitLife-AI) by
Nishchay Sharma (`shinzoxD`) and retains the project's MIT license notice.

AI-generated output is educational and is not medical advice.
