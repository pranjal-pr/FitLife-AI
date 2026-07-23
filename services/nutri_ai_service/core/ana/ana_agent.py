"""
Ana - RAG-based nutrition and recovery assistant for AI Fit Pro.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "nutri-ai"

INGREDIENT_PREFIXES = [
    "i have",
    "i've got",
    "i got",
    "my ingredients are",
    "ingredients:",
    "here are my ingredients",
]

MEAL_PLAN_KEYWORDS = [
    "meal plan",
    "diet plan",
    "recipe",
    "recipes",
    "what can i make",
    "what should i cook",
    "what should i eat",
    "breakfast ideas",
    "lunch ideas",
    "dinner ideas",
    "snack ideas",
    "make with",
    "cook with",
]

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "be",
    "can",
    "for",
    "from",
    "get",
    "give",
    "hello",
    "help",
    "hey",
    "hi",
    "how",
    "i",
    "if",
    "im",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "please",
    "should",
    "tell",
    "that",
    "the",
    "to",
    "us",
    "want",
    "what",
    "with",
    "you",
    "your",
}

GREETING_RE = re.compile(
    r"^(hi+|hello+|hey+|yo+|sup+|hola+|good morning|good afternoon|good evening|how are you|what'?s up|whats up)[!. ]*$",
    re.IGNORECASE,
)


def _load_json(filename: str) -> Any:
    path = DATA_DIR / filename
    if not path.exists():
        return [] if filename.endswith("chunks.json") else {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_book_chunks() -> List[Dict]:
    return _load_json("book_chunks.json")


def _load_diseases() -> Dict:
    return _load_json("diseases.json")


def _load_nutrient_limits() -> Dict:
    return _load_json("nutrient_limits.json")


def _flat_diseases(profile: Dict) -> List[str]:
    diseases = profile.get("medical_history", {}).get("diseases", [])
    names = []
    for disease in diseases:
        if isinstance(disease, dict):
            names.append(disease.get("name", ""))
        else:
            names.append(str(disease))
    return [name for name in names if name]


def _retrieve_chunks(
    search_terms: List[str],
    user_profile: Optional[Dict] = None,
    max_chunks: int = 6,
) -> List[str]:
    """Keyword retrieval over the nutrition book chunks."""
    book_chunks = _load_book_chunks()
    if not book_chunks:
        return []

    keywords = [term.strip().lower() for term in search_terms if term.strip()]
    if not keywords:
        keywords = ["nutrition", "meal", "recovery"]

    keywords.extend(
        [
            "protein",
            "carbohydrate",
            "fat",
            "fiber",
            "vitamin",
            "mineral",
            "calorie",
            "healthy",
            "nutrient",
            "diet",
        ]
    )

    if user_profile:
        diseases = user_profile.get("medical_history", {}).get("diseases", [])
        for disease in diseases:
            name = disease.get("name") if isinstance(disease, dict) else disease
            if name:
                keywords.append(str(name).lower())
        allergies = user_profile.get("allergies", [])
        keywords.extend([allergy.lower() for allergy in allergies if allergy])
        if user_profile.get("diet_type"):
            keywords.append(str(user_profile["diet_type"]).lower())
        if user_profile.get("goal"):
            keywords.append(str(user_profile["goal"]).lower())

    scored_results: List[tuple[int, str]] = []
    for chunk in book_chunks:
        text = chunk.get("content") if isinstance(chunk, dict) else chunk
        if not text:
            continue
        text_lower = str(text).lower()
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score:
            scored_results.append((score, str(text)))

    scored_results.sort(key=lambda item: item[0], reverse=True)

    results: List[str] = []
    seen = set()
    for _, text in scored_results:
        if text in seen:
            continue
        seen.add(text)
        results.append(text)
        if len(results) >= max_chunks:
            break
    return results


def _build_profile_block(user_profile: Optional[Dict]) -> str:
    if not user_profile:
        return ""

    return (
        "\n**User Profile:**\n"
        f"- Age: {user_profile.get('age', 'N/A')}\n"
        f"- Gender: {user_profile.get('gender', 'N/A')}\n"
        f"- Activity Level: {user_profile.get('activity_level', 'N/A')}\n"
        f"- Diet Type: {user_profile.get('diet_type', 'N/A')}\n"
        f"- Goal: {user_profile.get('goal', 'N/A')}\n"
        f"- Allergies: {', '.join(user_profile.get('allergies', [])) or 'None'}\n"
        f"- Medical Conditions: {', '.join(_flat_diseases(user_profile)) or 'None'}\n"
    )


def _build_meal_plan_system_prompt() -> str:
    return (
        "You are Ana, AI Fit Pro's friendly nutrition assistant. "
        "You are an expert dietitian trained on the Harvard Medical School "
        "Guide to Healthy Eating. Your job is to take the ingredients a user "
        "has available and suggest a practical, healthy diet plan they can "
        "prepare at home.\n\n"
        "Guidelines:\n"
        "- Always be encouraging and positive.\n"
        "- Suggest 2-3 meal ideas (breakfast / lunch / dinner as applicable).\n"
        "- For each meal give a short recipe outline (3-5 steps).\n"
        "- Mention approximate calorie and macro estimates per meal.\n"
        "- If the user has medical conditions or dietary restrictions, respect them.\n"
        "- If the ingredients are limited, suggest what single item they could add from the store to round out nutrition.\n"
        "- Keep responses concise but informative. Use markdown formatting.\n"
        "- End with a short motivational health tip.\n"
    )


def _build_general_system_prompt() -> str:
    return (
        "You are Ana, AI Fit Pro's friendly nutrition and recovery assistant. "
        "Answer the user's latest question directly and naturally.\n\n"
        "Guidelines:\n"
        "- Do not default to a full meal plan unless the user explicitly asks for one.\n"
        "- If the user asks a short greeting or casual question, reply briefly and invite them to share their goal.\n"
        "- If the user asks about macros, recovery, foods, labels, or ingredients, answer that question directly.\n"
        "- Offer concise meal suggestions only when they are relevant to the request.\n"
        "- Respect dietary restrictions, allergies, and medical conditions.\n"
        "- Keep the response practical, helpful, and easy to scan.\n"
        "- Use markdown only when it improves readability.\n"
    )


def _build_meal_plan_user_prompt(
    ingredients: List[str],
    user_profile: Optional[Dict],
    knowledge_context: str,
    diseases_context: str,
    nutrient_limits_context: str,
    latest_message: str = "",
) -> str:
    profile_block = _build_profile_block(user_profile)
    ingredients_str = ", ".join(ingredients) if ingredients else latest_message

    return (
        f"The user currently has these ingredients: **{ingredients_str}**\n"
        f"{profile_block}\n"
        f"**Relevant Nutrition Knowledge (from Harvard Medical School):**\n"
        f"{knowledge_context}\n\n"
        f"**Disease-Specific Dietary Guidelines:**\n"
        f"{diseases_context}\n\n"
        f"**Daily Nutrient Limits:**\n"
        f"{nutrient_limits_context}\n\n"
        "Based on the above, suggest a healthy diet plan using the available ingredients. "
        "Be specific with portion sizes and preparation methods."
    )


def _build_general_user_prompt(
    latest_message: str,
    user_profile: Optional[Dict],
    knowledge_context: str,
    diseases_context: str,
    nutrient_limits_context: str,
) -> str:
    profile_block = _build_profile_block(user_profile)

    return (
        f"The user's latest message is: **{latest_message}**\n"
        f"{profile_block}\n"
        f"**Relevant Nutrition Knowledge (from Harvard Medical School):**\n"
        f"{knowledge_context}\n\n"
        f"**Disease-Specific Dietary Guidelines:**\n"
        f"{diseases_context}\n\n"
        f"**Daily Nutrient Limits:**\n"
        f"{nutrient_limits_context}\n\n"
        "Respond directly to the user's request. If they ask a general question, answer it plainly. "
        "If they ask for quick food ideas, suggest concise options instead of a full-day meal plan unless they request one."
    )


GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


def _call_groq(messages: List[Dict], api_key: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error = ""
    for model in GROQ_MODELS:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.45,
            "max_tokens": 1500,
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=45)
            if response.ok:
                return response.json()["choices"][0]["message"]["content"]
            last_error = f"{model}: {response.status_code} {response.text[:200]}"
        except requests.exceptions.Timeout:
            last_error = f"{model}: timeout"
        except Exception as exc:
            last_error = f"{model}: {exc}"

    return f"I'm sorry, I couldn't generate a response right now. Last error: {last_error}"


def _extract_ingredients(text: str) -> List[str]:
    """Best-effort extraction of ingredient names from free-form text."""
    cleaned = text.lower().strip()
    for prefix in INGREDIENT_PREFIXES:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip(" :,")

    for marker in [
        "what can i make",
        "what should i cook",
        "what should i eat",
        "make with",
        "cook with",
    ]:
        if marker in cleaned:
            cleaned = cleaned.split(marker, 1)[0].strip(" .,!?:;")

    if "," in cleaned:
        parts = [part.strip() for part in cleaned.split(",")]
    elif " and " in cleaned:
        parts = [part.strip() for part in cleaned.replace(" and ", ",").split(",")]
    else:
        parts = cleaned.split()

    ingredients = []
    for part in parts:
        normalized = re.sub(r"^[^a-z0-9]+|[^a-z0-9 -]+$", "", part).strip()
        if normalized and len(normalized) < 60:
            ingredients.append(normalized)
    return ingredients


def _extract_query_terms(text: str) -> List[str]:
    terms = re.findall(r"[a-zA-Z][a-zA-Z0-9'-]*", text.lower())
    filtered = []
    for term in terms:
        if len(term) < 2 or term in STOPWORDS:
            continue
        filtered.append(term)
    return filtered[:20]


def _looks_like_ingredient_list(message: str, ingredients: List[str]) -> bool:
    lowered = message.lower().strip()
    if any(lowered.startswith(prefix) for prefix in INGREDIENT_PREFIXES):
        return True

    word_count = len(re.findall(r"[a-zA-Z0-9'-]+", lowered))
    return len(ingredients) >= 3 and ("," in lowered or " and " in lowered) and word_count <= 20


def _is_greeting_or_smalltalk(message: str) -> bool:
    return bool(GREETING_RE.match(message.strip()))


def _is_explicit_meal_plan_request(message: str, ingredients: List[str]) -> bool:
    lowered = message.lower().strip()
    if any(keyword in lowered for keyword in MEAL_PLAN_KEYWORDS):
        return True
    return _looks_like_ingredient_list(message, ingredients)


def _smalltalk_reply(user_profile: Optional[Dict] = None) -> str:
    name = (user_profile or {}).get("name")
    greeting = f"Hi {name}," if name else "Hi,"
    return (
        f"{greeting} I'm AI Fit Pro Coach. I can help with meals, macros, ingredients, "
        "recovery nutrition, and food-label questions. Tell me what you want help with."
    )


def chat(
    message: str,
    history: Optional[List[Dict]] = None,
    user_profile: Optional[Dict] = None,
    api_key: Optional[str] = None,
) -> str:
    """Main entry point for nutrition and recovery chat."""
    ingredients = _extract_ingredients(message)
    query_terms = _extract_query_terms(message)

    if _is_greeting_or_smalltalk(message):
        return _smalltalk_reply(user_profile)

    api_key = api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        return (
            "Ana is not configured yet - the GROQ_API_KEY environment variable is missing. "
            "Please ask the admin to set it up."
        )

    meal_plan_mode = _is_explicit_meal_plan_request(message, ingredients)
    search_terms = ingredients if meal_plan_mode else query_terms
    if not search_terms:
        search_terms = ingredients or ["nutrition", "meal", "recovery"]

    chunks = _retrieve_chunks(search_terms, user_profile)
    knowledge_context = "\n---\n".join(chunks[:6]) if chunks else "No specific knowledge retrieved."

    diseases_data = _load_diseases()
    user_diseases = _flat_diseases(user_profile) if user_profile else []
    disease_entries = []
    for disease_name in user_diseases:
        key = disease_name.lower()
        if key in diseases_data:
            info = diseases_data[key]
            disease_entries.append(
                f"**{disease_name}**: {info.get('recommended_diet', '')} "
                f"Risks: {json.dumps(info.get('nutrient_risks', {}))}"
            )
    diseases_context = "\n".join(disease_entries) if disease_entries else "No specific disease constraints."

    nutrient_limits = _load_nutrient_limits()
    nutrient_limits_context = json.dumps(nutrient_limits.get("general", {}), indent=2)

    if meal_plan_mode:
        system_prompt = _build_meal_plan_system_prompt()
        user_prompt = _build_meal_plan_user_prompt(
            ingredients=ingredients,
            user_profile=user_profile,
            knowledge_context=knowledge_context,
            diseases_context=diseases_context,
            nutrient_limits_context=nutrient_limits_context,
            latest_message=message,
        )
    else:
        system_prompt = _build_general_system_prompt()
        user_prompt = _build_general_user_prompt(
            latest_message=message,
            user_profile=user_profile,
            knowledge_context=knowledge_context,
            diseases_context=diseases_context,
            nutrient_limits_context=nutrient_limits_context,
        )

    messages: List[Dict] = [{"role": "system", "content": system_prompt}]

    if history:
        for entry in history[-8:]:
            messages.append(
                {
                    "role": entry.get("role", "user"),
                    "content": entry.get("content", ""),
                }
            )

    messages.append({"role": "user", "content": user_prompt})

    return _call_groq(messages, api_key)
