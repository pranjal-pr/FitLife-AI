"""
Native Hugging Face Gradio interface for the AI Fit Pro features.

The full product uses a Next.js frontend and Flask API. This module provides a
Space-friendly demo that runs the nutrition, coaching, and workout pipelines
directly through Gradio.
"""

from __future__ import annotations

import mimetypes
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any

import gradio as gr

os.environ.setdefault("FITLIFE_RUNTIME", "huggingface")
RUNTIME_ROOT = Path(tempfile.gettempdir()) / "fitlife-gradio"
RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(RUNTIME_ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(RUNTIME_ROOT / "matplotlib"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

from gateway.nutri_ai_lite import (  # noqa: E402
    calculate_health_metrics,
    extract_nutrition_from_image,
    generate_score,
)
from services.nutri_ai_service.core.ana.ana_agent import chat as nutrition_chat  # noqa: E402

try:
    import spaces

    # Keep the ZeroGPU reservation below the free-tier maximum. A 180-second
    # request is weighted as 270 seconds on the selected hardware and is
    # rejected before the workout function starts.
    gpu_task = spaces.GPU(duration=60)
except ImportError:
    # The decorator is supplied by ZeroGPU. Keeping a local no-op makes the
    # same app testable on ordinary CPU machines.
    def gpu_task(function):
        return function


EXERCISES = {
    "Regular Deadlift": "regular_deadlift",
    "Sumo Deadlift": "sumo_deadlift",
    "Squat": "squat",
    "Romanian Deadlift": "romanian_deadlift",
    "Zercher Squat": "zercher_squat",
    "Front Squat": "front_squat",
}

CUSTOM_CSS = """
.gradio-container {
  max-width: 1180px !important;
  margin: 0 auto !important;
}
.fitlife-hero {
  padding: 26px 28px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 24px;
  background:
    radial-gradient(circle at 10% 10%, rgba(249, 115, 22, 0.20), transparent 36%),
    radial-gradient(circle at 90% 0%, rgba(16, 185, 129, 0.16), transparent 34%);
}
.fitlife-hero h1 {
  margin: 0 0 8px;
  font-size: clamp(2rem, 5vw, 3.6rem);
  line-height: 1;
}
.fitlife-muted {
  color: #94a3b8;
}
"""

APP_THEME = gr.themes.Soft(primary_hue="orange", secondary_hue="emerald")


def _split_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in re.split(r"[,;\n]", value) if item.strip()]


def _profile(
    age: float,
    gender: str,
    height_cm: float,
    weight_kg: float,
    activity_level: str,
    goal: str,
    diet_type: str,
    allergies: str,
    medical_conditions: str,
) -> dict[str, Any]:
    conditions = _split_list(medical_conditions)
    return {
        "age": int(age),
        "gender": gender.lower(),
        "height_cm": float(height_cm),
        "weight_kg": float(weight_kg),
        "activity_level": activity_level,
        "goal": goal,
        "diet_type": diet_type,
        "allergies": _split_list(allergies),
        "medical_history": {"diseases": conditions},
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def analyze_nutrition(
    image_path: str | None,
    age: float,
    gender: str,
    height_cm: float,
    weight_kg: float,
    activity_level: str,
    goal: str,
    diet_type: str,
    allergies: str,
    medical_conditions: str,
) -> tuple[dict[str, Any], dict[str, Any], float, str]:
    """Extract a food label and generate a profile-aware nutrition score."""
    if not image_path:
        raise gr.Error("Upload a nutrition-label image first.")

    path = Path(image_path)
    if not path.exists():
        raise gr.Error("The uploaded image is no longer available. Upload it again.")

    mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    nutrition = extract_nutrition_from_image(path.read_bytes(), mime_type)
    if nutrition.get("error"):
        raise gr.Error(str(nutrition["error"]))

    user_profile = _profile(
        age,
        gender,
        height_cm,
        weight_kg,
        activity_level,
        goal,
        diet_type,
        allergies,
        medical_conditions,
    )
    health_metrics = calculate_health_metrics(user_profile)
    score, explanation = generate_score(user_profile, nutrition, health_metrics)
    return (
        _json_safe(nutrition),
        _json_safe(health_metrics),
        float(score),
        explanation,
    )


def _normalize_history(history: list[Any] | None) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for entry in history or []:
        if isinstance(entry, dict):
            role = str(entry.get("role", "user"))
            content = entry.get("content", "")
            if isinstance(content, str):
                normalized.append({"role": role, "content": content})
        elif isinstance(entry, (list, tuple)) and len(entry) == 2:
            if entry[0]:
                normalized.append({"role": "user", "content": str(entry[0])})
            if entry[1]:
                normalized.append({"role": "assistant", "content": str(entry[1])})
    return normalized


def coach_reply(message: str, history: list[Any] | None) -> str:
    """Generate a nutrition and recovery response for Gradio ChatInterface."""
    message = (message or "").strip()
    if not message:
        return "Tell me what you would like help with."
    return nutrition_chat(message=message, history=_normalize_history(history))


@gpu_task
def analyze_workout(
    video_path: str | None,
    exercise_label: str,
) -> tuple[str | None, dict[str, Any], str]:
    """Analyze a workout clip with the selected YOLO checkpoint."""
    if not video_path:
        raise gr.Error("Upload a workout video first.")
    if exercise_label not in EXERCISES:
        raise gr.Error("Choose a supported exercise.")

    from services.muscle_ai_service.core.analysis import format_analysis_result
    from services.muscle_ai_service.core.models.yolo import get_yolo_model
    from services.muscle_ai_service.utils.video import process_video

    source = Path(video_path)
    if not source.exists():
        raise gr.Error("The uploaded video is no longer available. Upload it again.")

    exercise_type = EXERCISES[exercise_label]
    output_root = Path(tempfile.gettempdir()) / "fitlife-gradio"
    output_root.mkdir(parents=True, exist_ok=True)
    output_path = output_root / f"{uuid.uuid4().hex}.mp4"

    try:
        model = get_yolo_model(exercise_type)
        metrics = process_video(
            str(source),
            str(output_path),
            None,
            exercise_type,
            model,
        )
        result = _json_safe(format_analysis_result(exercise_type, metrics))
    except Exception as error:
        raise gr.Error(f"Workout analysis failed: {error}") from error

    feedback = result.get("feedback") or []
    summary = (
        f"### {result['exercise_label']}\n"
        f"**Form score:** {result['form_score']}/100  \n"
        f"**Repetitions:** {result['reps']}  \n"
        f"**Frames analyzed:** {result['frames_analyzed']}\n\n"
        + "\n".join(f"- {item}" for item in feedback)
    )
    display_video = str(output_path) if output_path.exists() else str(source)
    return display_video, result, summary


def build_demo() -> gr.Blocks:
    with gr.Blocks(
        title="AI Fit Pro",
        delete_cache=(3600, 3600),
    ) as demo:
        gr.HTML(
            """
            <section class="fitlife-hero">
              <p>PERSONAL AI FITNESS LAB</p>
              <h1>Train smarter. Eat with context.</h1>
              <p class="fitlife-muted">
                Scan nutrition labels, review workout form, and ask a
                profile-aware nutrition and recovery coach.
              </p>
            </section>
            """
        )

        with gr.Tab("Fuel Scan"):
            gr.Markdown(
                "Upload a clear nutrition label and add your basic profile for a personalized score."
            )
            with gr.Row():
                with gr.Column(scale=1):
                    nutrition_image = gr.Image(
                        label="Nutrition label",
                        type="filepath",
                        sources=["upload", "webcam"],
                    )
                    with gr.Row():
                        age = gr.Number(label="Age", value=28, minimum=13, maximum=100)
                        gender = gr.Dropdown(
                            ["Male", "Female"],
                            value="Male",
                            label="Gender",
                        )
                    with gr.Row():
                        height = gr.Number(
                            label="Height (cm)",
                            value=175,
                            minimum=100,
                            maximum=250,
                        )
                        weight = gr.Number(
                            label="Weight (kg)",
                            value=72,
                            minimum=30,
                            maximum=300,
                        )
                    activity = gr.Dropdown(
                        ["sedentary", "light", "moderate", "active", "very_active"],
                        value="moderate",
                        label="Activity level",
                    )
                    goal = gr.Dropdown(
                        ["lose weight", "maintain weight", "gain weight"],
                        value="maintain weight",
                        label="Goal",
                    )
                    diet = gr.Dropdown(
                        ["balanced", "vegetarian", "vegan", "high protein", "low carb"],
                        value="balanced",
                        label="Diet type",
                    )
                    allergies = gr.Textbox(
                        label="Allergies",
                        placeholder="peanuts, dairy",
                    )
                    conditions = gr.Textbox(
                        label="Medical conditions",
                        placeholder="diabetes, hypertension",
                    )
                    scan_button = gr.Button("Analyze label", variant="primary")

                with gr.Column(scale=1):
                    score = gr.Number(label="Consumability score")
                    explanation = gr.Markdown()
                    with gr.Accordion("Extracted nutrition", open=True):
                        nutrition_json = gr.JSON(label="Nutrition")
                    with gr.Accordion("Calculated health metrics", open=False):
                        metrics_json = gr.JSON(label="Health metrics")

            scan_button.click(
                fn=analyze_nutrition,
                inputs=[
                    nutrition_image,
                    age,
                    gender,
                    height,
                    weight,
                    activity,
                    goal,
                    diet,
                    allergies,
                    conditions,
                ],
                outputs=[nutrition_json, metrics_json, score, explanation],
                api_name="analyze_nutrition",
            )

        with gr.Tab("Form Coach"):
            gr.Markdown(
                "Upload a short, well-lit clip with your full body visible. "
                "The selected YOLO model scores movement confidence and counts clear repetitions."
            )
            with gr.Row():
                with gr.Column():
                    workout_video = gr.Video(label="Workout video", sources=["upload"])
                    exercise = gr.Dropdown(
                        list(EXERCISES),
                        value="Squat",
                        label="Exercise",
                    )
                    workout_button = gr.Button("Analyze workout", variant="primary")
                with gr.Column():
                    processed_video = gr.Video(label="Analyzed video")
                    workout_summary = gr.Markdown()
                    workout_json = gr.JSON(label="Detailed metrics")

            workout_button.click(
                fn=analyze_workout,
                inputs=[workout_video, exercise],
                outputs=[processed_video, workout_json, workout_summary],
                api_name="analyze_workout",
            )

        with gr.Tab("AI Fit Pro Coach"):
            gr.Markdown(
                "Ask about meal planning, ingredients, macros, food labels, or recovery nutrition."
            )
            gr.ChatInterface(
                fn=coach_reply,
                examples=[
                    "Build a high-protein vegetarian dinner from lentils, spinach, and rice.",
                    "What should I eat after a heavy squat session?",
                    "Help me reduce sodium without making my meals bland.",
                ],
                api_name="coach",
            )

        gr.Markdown(
            "AI Fit Pro is based on the FitLife-AI project. AI output is educational and is not medical advice."
        )

    return demo


demo = build_demo()


if __name__ == "__main__":
    demo.queue(default_concurrency_limit=1).launch(
        theme=APP_THEME,
        css=CUSTOM_CSS,
    )
