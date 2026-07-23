'use client';

import { useState } from 'react';
import { analyzeWorkout } from '@/lib/gradio';
import type { MuscleAnalysisResult } from '@/lib/types';
import ExerciseSelect from '@/components/muscle-ai/ExerciseSelect';
import VideoUpload from '@/components/muscle-ai/VideoUpload';
import AnalysisResults from '@/components/muscle-ai/AnalysisResults';
import Button from '@/components/ui/Button';
import Alert from '@/components/ui/Alert';

export default function MuscleAIPage() {
  const [exercise, setExercise] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<MuscleAnalysisResult | null>(null);

  async function handleUpload() {
    if (!file || !exercise) return;
    setUploading(true);
    setError('');
    setResult(null);

    try {
      setResult(await analyzeWorkout(file, exercise));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  }

  const isComplete = Boolean(result);

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 sm:py-16">
      <div className="mb-12 text-center">
        <span className="mb-4 inline-block rounded-full border border-accent/30 bg-accent-glow px-3 py-1 text-xs font-semibold text-accent">
          FORM COACH
        </span>
        <h1 className="font-display text-3xl font-bold sm:text-4xl">
          Upload a set. Get <span className="text-accent">actionable coaching cues.</span>
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-text-secondary">
          Form Coach uses pose analysis to score movement quality, estimate reps, and highlight technique risks before they become habits.
        </p>
      </div>

      {error && <Alert variant="error" className="mb-6">{error}</Alert>}

      <div className="mb-8">
        <h2 className="mb-4 font-semibold">1. Choose the lift pattern</h2>
        <ExerciseSelect value={exercise} onChange={setExercise} />
      </div>

      <div className="mb-8">
        <h2 className="mb-4 font-semibold">2. Upload your video</h2>
        <VideoUpload onFileSelected={setFile} disabled={!exercise} />
      </div>

      {!isComplete && (
        <Button
          onClick={handleUpload}
          loading={uploading}
          disabled={!exercise || !file}
          size="lg"
          className="w-full"
        >
          {uploading ? 'Analyzing movement...' : 'Generate Coaching Report'}
        </Button>
      )}

      {uploading && !isComplete && (
        <div className="mt-6 flex flex-col items-center text-center">
          <div className="mb-3 h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          <p className="text-sm text-text-secondary">Processing your set. This can take up to a minute for longer clips.</p>
        </div>
      )}

      {isComplete && result && (
        <div className="mt-8">
          <h2 className="mb-4 font-semibold">Coaching Report</h2>
          <AnalysisResults data={result} />
          <Button
            variant="secondary"
            className="mt-6 w-full"
            onClick={() => {
              setResult(null);
              setFile(null);
              setExercise('');
            }}
          >
            Analyze Another Set
          </Button>
        </div>
      )}

    </div>
  );
}
