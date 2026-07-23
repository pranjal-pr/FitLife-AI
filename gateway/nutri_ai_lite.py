"""
Lightweight Nutri AI integration for the gateway.
Uses Groq vision models for label OCR and text models for scoring.
No heavy ML dependencies (no easyocr, torch, etc.).
"""

import os
import json
import base64
import requests
from pathlib import Path
from typing import Dict, Optional, Tuple

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "nutri-ai"

GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]

VISION_MODELS = [
    "qwen/qwen3.6-27b",
]


def _load_json(filename: str):
    path = DATA_DIR / filename
    if not path.exists():
        return [] if "chunks" in filename else {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _groq_api_key() -> str:
    return os.getenv("GROQ_API_KEY", "")


def _call_groq_text(messages: list, api_key: str) -> Optional[str]:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    for model in GROQ_MODELS:
        try:
            resp = requests.post(url, headers=headers, json={
                "model": model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1500,
            }, timeout=45)
            if resp.ok:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            continue
    return None


def _call_groq_vision(
    image_b64: str,
    mime_type: str,
    prompt: str,
    api_key: str,
) -> Tuple[Optional[str], Optional[str]]:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}},
        ],
    }]

    last_error = None
    for model in VISION_MODELS:
        try:
            resp = requests.post(url, headers=headers, json={
                "model": model,
                "messages": messages,
                "temperature": 0.1,
                "max_completion_tokens": 1000,
                "reasoning_effort": "none",
                "response_format": {"type": "json_object"},
            }, timeout=45)
            if resp.ok:
                return resp.json()["choices"][0]["message"]["content"], None

            try:
                error_payload = resp.json().get("error", {})
                last_error = error_payload.get("message") or f"HTTP {resp.status_code}"
            except (ValueError, AttributeError):
                last_error = f"HTTP {resp.status_code}"
        except requests.RequestException as error:
            last_error = f"Groq request failed: {error.__class__.__name__}"
            continue
    return None, last_error


def extract_nutrition_from_image(image_bytes: bytes, mime_type: str) -> Dict:
    """Use Groq vision to extract nutrition data from a label image."""
    api_key = _groq_api_key()
    if not api_key:
        return {"error": "GROQ_API_KEY not set"}

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt = (
        "Extract the nutrition facts from this food label image. "
        "Return ONLY a JSON object with these numeric fields (use 0 if not found): "
        "calories, protein, carbs, sugars, fat, saturated_fat, trans_fat, sodium, fiber. "
        "Values should be numbers only (no units). "
        "Example: {\"calories\": 250, \"protein\": 8, \"carbs\": 30, \"sugars\": 12, "
        "\"fat\": 10, \"saturated_fat\": 3, \"trans_fat\": 0, \"sodium\": 480, \"fiber\": 3}"
    )

    result, vision_error = _call_groq_vision(image_b64, mime_type, prompt, api_key)
    if not result:
        message = "Could not extract nutrition info from image"
        if vision_error:
            message = f"{message}: {vision_error}"
        return {"error": message}

    try:
        start = result.find("{")
        end = result.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(result[start:end])
    except (json.JSONDecodeError, ValueError):
        pass

    return {"error": "Could not parse nutrition data from AI response", "raw": result[:500]}


def calculate_health_metrics(profile: Dict) -> Dict:
    """Pure-Python health metrics calculation (no heavy deps)."""
    height_cm = profile.get("height_cm", 170)
    weight_kg = profile.get("weight_kg", 70)
    age = profile.get("age", 30)
    gender = profile.get("gender", "male")

    height_m = height_cm / 100
    bmi = round(weight_kg / (height_m * height_m), 2)

    if bmi < 18.5:
        bmi_cat = "Underweight"
    elif bmi < 25:
        bmi_cat = "Normal weight"
    elif bmi < 30:
        bmi_cat = "Overweight"
    else:
        bmi_cat = "Obesity"

    if gender.lower() == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

    multipliers = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "very_active": 1.9}
    tdee = round(bmr * multipliers.get(profile.get("activity_level", "moderate"), 1.55))

    goal = profile.get("goal", "maintain weight")
    if goal == "lose weight":
        cal_target = tdee - 500
    elif goal == "gain weight":
        cal_target = tdee + 500
    else:
        cal_target = tdee

    return {
        "bmi": bmi,
        "bmi_category": bmi_cat,
        "bmr": round(bmr),
        "tdee": tdee,
        "calorie_target": cal_target,
        "macros": {
            "carbs_g": round((cal_target * 0.4) / 4),
            "protein_g": round((cal_target * 0.3) / 4),
            "fat_g": round((cal_target * 0.3) / 9),
        },
    }


def generate_score(user_profile: Dict, nutrition_info: Dict, health_metrics: Dict) -> Tuple[int, str]:
    """Call Groq to generate a consumability score and explanation."""
    api_key = _groq_api_key()
    if not api_key:
        return 50, "Scoring unavailable (GROQ_API_KEY not set)."

    book_chunks = _load_json("book_chunks.json")
    diseases_data = _load_json("diseases.json")

    keywords = list(nutrition_info.keys())
    if user_profile.get("allergies"):
        keywords.extend(user_profile["allergies"])
    if user_profile.get("diet_type"):
        keywords.append(user_profile["diet_type"])
    keywords = [str(k).lower() for k in keywords if k]

    relevant = []
    for chunk in book_chunks:
        text = chunk.get("content") if isinstance(chunk, dict) else chunk
        if not text:
            continue
        if any(kw in str(text).lower() for kw in keywords):
            relevant.append(str(text))
            if len(relevant) >= 4:
                break

    nutrition_str = "\n".join(f"{k}: {v}" for k, v in nutrition_info.items())
    knowledge_str = "\n\n".join(relevant) if relevant else "No specific knowledge."

    user_diseases = []
    for d in user_profile.get("medical_history", {}).get("diseases", []):
        name = d.get("name") if isinstance(d, dict) else d
        if name:
            user_diseases.append(str(name))

    prompt = f"""You are a nutritional expert. Analyze this food's nutrition against the user's profile and assign a Consumability Score from 0-100.

USER PROFILE:
Age: {user_profile.get('age', 'N/A')}, Gender: {user_profile.get('gender', 'N/A')}
Activity: {user_profile.get('activity_level', 'N/A')}, Goal: {user_profile.get('goal', 'N/A')}
Diet: {user_profile.get('diet_type', 'N/A')}
Allergies: {', '.join(user_profile.get('allergies', [])) or 'None'}
Medical Conditions: {', '.join(user_diseases) or 'None'}

HEALTH METRICS:
BMI: {health_metrics.get('bmi')}, TDEE: {health_metrics.get('tdee')} kcal
Calorie Target: {health_metrics.get('calorie_target')} kcal

NUTRITION (per serving):
{nutrition_str}

RELEVANT KNOWLEDGE:
{knowledge_str}

Respond in this exact format:
SCORE: [number 0-100]

EXPLANATION:
[detailed explanation]

RECOMMENDATIONS:
[specific recommendations]"""

    messages = [
        {"role": "system", "content": "You are a nutritional expert that provides personalized health advice."},
        {"role": "user", "content": prompt},
    ]

    response = _call_groq_text(messages, api_key)
    if not response:
        return 50, "Could not generate analysis. Using default score."

    score = 50
    try:
        for line in response.split("\n"):
            if line.strip().upper().startswith("SCORE:"):
                num = "".join(c for c in line.split(":", 1)[1] if c.isdigit())
                if num:
                    score = max(0, min(100, int(num)))
                break
    except Exception:
        pass

    return score, response
