import { Client } from '@gradio/client';
import type { NutritionProfile } from './nutri-profile';
import type { MuscleAnalysisResult } from './types';

const SPACE_ID =
  process.env.NEXT_PUBLIC_GRADIO_SPACE_ID || 'praanjalpradhan/AI-FIT-PRO';

let clientPromise: Promise<Client> | null = null;

function getClient() {
  if (!clientPromise) {
    clientPromise = Client.connect(SPACE_ID).catch((error) => {
      clientPromise = null;
      throw error;
    });
  }
  return clientPromise;
}

function asRecord(value: unknown): Record<string, unknown> {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }

  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value);
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        return parsed as Record<string, unknown>;
      }
    } catch {
      // Gradio normally returns JSON components as objects.
    }
  }

  return {};
}

function responseData(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [value];
}

function normalizeError(error: unknown, fallback: string) {
  if (error instanceof Error && error.message) {
    return new Error(error.message);
  }
  if (typeof error === 'string' && error) {
    return new Error(error);
  }
  if (error && typeof error === 'object') {
    const details = error as {
      message?: unknown;
      error?: unknown;
      detail?: unknown;
    };
    for (const value of [details.message, details.error, details.detail]) {
      if (typeof value === 'string' && value.trim()) {
        return new Error(value);
      }
    }
  }
  return new Error(fallback);
}

function normalizeGender(value: string) {
  return value.toLowerCase() === 'female' ? 'Female' : 'Male';
}

function normalizeGoal(value: string) {
  const goals: Record<string, string> = {
    lose: 'lose weight',
    loss: 'lose weight',
    'weight loss': 'lose weight',
    maintain: 'maintain weight',
    maintenance: 'maintain weight',
    gain: 'gain weight',
    'weight gain': 'gain weight',
  };
  return goals[value.toLowerCase()] || value.toLowerCase();
}

function normalizeDiet(value: string) {
  const diets: Record<string, string> = {
    omnivore: 'balanced',
    omnivorous: 'balanced',
    none: 'balanced',
    'high-protein': 'high protein',
    'low-carb': 'low carb',
  };
  return diets[value.toLowerCase()] || value.toLowerCase();
}

function fileUrl(value: unknown): string | null {
  if (typeof value === 'string') return value;
  if (!value || typeof value !== 'object') return null;

  const file = value as { url?: unknown };
  return typeof file.url === 'string' ? file.url : null;
}

const exerciseLabels: Record<string, string> = {
  regular_deadlift: 'Regular Deadlift',
  sumo_deadlift: 'Sumo Deadlift',
  squat: 'Squat',
  romanian_deadlift: 'Romanian Deadlift',
  zercher_squat: 'Zercher Squat',
  front_squat: 'Front Squat',
};

export interface NutritionAnalysis {
  nutrition: Record<string, unknown>;
  health_metrics: Record<string, unknown>;
  score: number;
  explanation: string;
}

export async function analyzeNutrition(
  image: File,
  profile: NutritionProfile,
): Promise<NutritionAnalysis> {
  try {
    const client = await getClient();
    const result = await client.predict<unknown[]>('/analyze_nutrition', {
      image_path: image,
      age: profile.age,
      gender: normalizeGender(profile.gender),
      height_cm: profile.height_cm,
      weight_kg: profile.weight_kg,
      activity_level: profile.activity_level,
      goal: normalizeGoal(profile.goal),
      diet_type: normalizeDiet(profile.diet_type),
      allergies: profile.allergies.join(', '),
      medical_conditions: profile.medical_history.diseases.join(', '),
    });
    const data = responseData(result.data);

    return {
      nutrition: asRecord(data[0]),
      health_metrics: asRecord(data[1]),
      score: Number(data[2] ?? 0),
      explanation: typeof data[3] === 'string' ? data[3] : '',
    };
  } catch (error) {
    throw normalizeError(error, 'Nutrition analysis failed.');
  }
}

export async function analyzeWorkout(
  video: File,
  exercise: string,
): Promise<MuscleAnalysisResult> {
  try {
    const client = await getClient();
    const result = await client.predict<unknown[]>('/analyze_workout', {
      video_path: video,
      exercise_label: exerciseLabels[exercise] || exercise,
    });
    const data = responseData(result.data);
    const metrics = asRecord(data[1]);

    return {
      ...(metrics as unknown as MuscleAnalysisResult),
      video_url: fileUrl(data[0]),
    };
  } catch (error) {
    throw normalizeError(error, 'Workout analysis failed.');
  }
}

export async function askCoach(message: string): Promise<string> {
  try {
    const client = await getClient();
    const result = await client.predict<unknown[]>('/coach', { message });
    const data = responseData(result.data);
    const reply = data[0];

    if (typeof reply !== 'string' || !reply.trim()) {
      throw new Error('The coach returned an empty response.');
    }
    return reply;
  } catch (error) {
    throw normalizeError(error, 'The coach is temporarily unavailable.');
  }
}
