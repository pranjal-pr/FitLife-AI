'use client';

import { useState, useRef, type DragEvent } from 'react';
import { useRouter } from 'next/navigation';
import { analyzeNutrition, type NutritionAnalysis } from '@/lib/gradio';
import { useAuth } from '@/lib/auth';
import { getPreferredNutritionProfile, saveNutritionProfile } from '@/lib/nutri-profile';
import Button from '@/components/ui/Button';
import Alert from '@/components/ui/Alert';

export default function UploadDropzone() {
  const router = useRouter();
  const { user } = useAuth();
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState<'upload' | 'extracted'>('upload');
  const [analysis, setAnalysis] = useState<NutritionAnalysis | null>(null);

  function handleFile(nextFile: File) {
    if (!nextFile.type.startsWith('image/')) {
      setError('Please upload an image file.');
      return;
    }
    setFile(nextFile);
    setError('');
    setPreview(URL.createObjectURL(nextFile));
    setStep('upload');
    setAnalysis(null);
  }

  function onDrop(event: DragEvent) {
    event.preventDefault();
    setDragging(false);
    if (event.dataTransfer.files[0]) handleFile(event.dataTransfer.files[0]);
  }

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      const userProfile = getPreferredNutritionProfile(user);
      saveNutritionProfile(userProfile);
      const result = await analyzeNutrition(file, userProfile);
      setAnalysis(result);
      setStep('extracted');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Upload failed';
      setError(message);
    } finally {
      setUploading(false);
    }
  }

  async function handleAnalyze() {
    if (!analysis) return;
    setUploading(true);
    setError('');
    try {
      sessionStorage.setItem('nutri_result', JSON.stringify(analysis));
      router.push('/nutri-ai/results');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Analysis failed';
      setError(message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-6">
      {error && <Alert variant="error">{error}</Alert>}

      <div
        onClick={() => fileRef.current?.click()}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center transition-colors sm:p-12 ${
          dragging ? 'border-accent bg-accent-glow' : 'border-border hover:border-border-hover'
        }`}
      >
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(event) => event.target.files?.[0] && handleFile(event.target.files[0])}
        />

        {preview ? (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img src={preview} alt="Preview" className="mb-4 max-h-64 w-full rounded-lg object-contain" />
        ) : (
          <svg className="mb-4 h-12 w-12 text-text-tertiary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M12 16V4m0 0-4 4m4-4 4 4" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M2 17l.621 2.485A2 2 0 0 0 4.561 21h14.878a2 2 0 0 0 1.94-1.515L22 17" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        )}
        <p className="text-sm text-text-secondary">{file ? file.name : 'Drop a nutrition label here or click to browse'}</p>
        <p className="mt-1 text-xs text-text-tertiary">JPG, PNG, WEBP up to 10 MB</p>
      </div>

      {step === 'upload' && (
        <Button onClick={handleUpload} loading={uploading} disabled={!file} size="lg" className="w-full">
          {uploading ? 'Extracting nutrition data...' : 'Extract Label Data'}
        </Button>
      )}

      {step === 'extracted' && analysis && (
        <div className="space-y-4">
          <div className="rounded-xl border border-border bg-bg-secondary p-6">
            <h3 className="mb-4 text-lg font-semibold">Extracted Nutrition Facts</h3>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {Object.entries(analysis.nutrition).map(([key, value]) => (
                <div key={key} className="rounded-lg bg-bg-tertiary p-3 text-center">
                  <div className="text-xs capitalize text-text-tertiary">{key.replace(/_/g, ' ')}</div>
                  <div className="text-lg font-bold">{String(value)}</div>
                </div>
              ))}
            </div>
          </div>
          <Button onClick={handleAnalyze} loading={uploading} size="lg" className="w-full">
            {uploading ? 'Scoring your label...' : 'Generate Fuel Fit Score'}
          </Button>
        </div>
      )}
    </div>
  );
}
