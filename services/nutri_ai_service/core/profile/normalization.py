"""Canonical profile values shared by web and Gradio nutrition flows."""

from __future__ import annotations

import re


def _normalized_choice(value: str | None) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[_-]+", " ", value or "").strip().lower())


def normalize_activity(value: str | None) -> str:
    choices = {
        "sedentary": "sedentary",
        "light": "light",
        "lightly active": "light",
        "moderate": "moderate",
        "moderately active": "moderate",
        "active": "active",
        "very active": "very_active",
        "extreme": "very_active",
        "extremely active": "very_active",
    }
    return choices.get(_normalized_choice(value), "moderate")


def normalize_goal(value: str | None) -> str:
    choices = {
        "lose": "lose weight",
        "loss": "lose weight",
        "lose weight": "lose weight",
        "weight loss": "lose weight",
        "maintain": "maintain weight",
        "maintenance": "maintain weight",
        "maintain weight": "maintain weight",
        "improve health": "maintain weight",
        "improve overall health": "maintain weight",
        "gain": "gain weight",
        "gain weight": "gain weight",
        "weight gain": "gain weight",
        "gain muscle": "gain weight",
        "muscle gain": "gain weight",
    }
    return choices.get(_normalized_choice(value), "maintain weight")


def normalize_diet(value: str | None) -> str:
    choices = {
        "omnivore": "balanced",
        "omnivorous": "balanced",
        "none": "balanced",
        "balanced": "balanced",
        "paleo": "balanced",
        "vegetarian": "vegetarian",
        "vegan": "vegan",
        "keto": "low carb",
        "ketogenic": "low carb",
        "high protein": "high protein",
        "low carb": "low carb",
    }
    return choices.get(_normalized_choice(value), "balanced")
