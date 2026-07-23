'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { apiFetch } from '@/lib/api';
import type { DashboardStats, ScanItem, WorkoutItem } from '@/lib/types';
import StatCard from '@/components/dashboard/StatCard';

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [scans, setScans] = useState<ScanItem[]>([]);
  const [workouts, setWorkouts] = useState<WorkoutItem[]>([]);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
      return;
    }
    if (!user) return;
    apiFetch<DashboardStats>('/dashboard/stats').then(setStats).catch(() => {});
    apiFetch<{ items: ScanItem[] }>('/user/scans?per_page=5').then((response) => setScans(response.items)).catch(() => {});
    apiFetch<{ items: WorkoutItem[] }>('/user/workouts?per_page=5').then((response) => setWorkouts(response.items)).catch(() => {});
  }, [user, authLoading, router]);

  if (authLoading || !user) return <div className="flex min-h-[60vh] items-center justify-center px-4 text-text-secondary">Loading...</div>;

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 sm:py-12">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold">Welcome back, {user.name}</h1>
          <p className="mt-1 text-text-secondary">Here is your AI Fit Pro performance snapshot.</p>
        </div>
        <Link
          href="/dashboard/settings"
          className="rounded-lg border border-border px-4 py-2 text-sm text-text-secondary transition-colors hover:border-border-hover hover:text-text-primary"
        >
          Settings
        </Link>
      </div>

      <div className="mb-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Health Score"
          value={stats?.health_score ?? 0}
          icon={<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>}
        />
        <StatCard
          label="Fuel Scans"
          value={stats?.total_scans ?? 0}
          sub={`Avg. ${stats?.avg_nutrition ?? 0}/100`}
          icon={<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" /><path d="M7 7h10M7 12h10M7 17h4" /></svg>}
        />
        <StatCard
          label="Form Sessions"
          value={stats?.total_workouts ?? 0}
          sub={`Avg. form ${stats?.avg_form ?? 0}/100`}
          icon={<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 8h1a4 4 0 0 1 0 8h-1M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z" /></svg>}
        />
        <StatCard
          label="Plan"
          value={stats?.plan ?? 'Starter'}
          sub={`${stats?.scans_this_month ?? 0} scans this month`}
          icon={<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" /></svg>}
        />
      </div>

      <div className="mb-12 grid gap-4 sm:grid-cols-3">
        <Link href="/nutri-ai" className="rounded-xl border border-border bg-bg-secondary p-6 text-center transition-all hover:border-accent/40 hover:shadow-lg hover:shadow-accent/5">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-accent/10 text-accent">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 12H3M16 6H3M16 18H3" /><path d="m19 10-4 4m0-4 4 4" /></svg>
          </div>
          <h3 className="font-semibold">Fuel Scan</h3>
          <p className="mt-1 text-sm text-text-secondary">Analyze a packaged label</p>
        </Link>
        <Link href="/muscle-ai" className="rounded-xl border border-border bg-bg-secondary p-6 text-center transition-all hover:border-accent/40 hover:shadow-lg hover:shadow-accent/5">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-accent/10 text-accent">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 8h1a4 4 0 0 1 0 8h-1M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z" /></svg>
          </div>
          <h3 className="font-semibold">Form Coach</h3>
          <p className="mt-1 text-sm text-text-secondary">Upload a workout check-in</p>
        </Link>
        <Link href="/ana" className="rounded-xl border border-border bg-bg-secondary p-6 text-center transition-all hover:border-accent/40 hover:shadow-lg hover:shadow-accent/5">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-accent/10 text-accent">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446A9 9 0 1 1 12 3z" /></svg>
          </div>
          <h3 className="font-semibold">AI Fit Pro Coach</h3>
          <p className="mt-1 text-sm text-text-secondary">Ask for meals and recovery advice</p>
        </Link>
      </div>

      <div className="grid gap-8 lg:grid-cols-2">
        <section>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-semibold">Recent Fuel Scans</h2>
            <Link href="/dashboard/history" className="text-sm text-accent hover:text-accent-hover">View all</Link>
          </div>
          {scans.length === 0 ? (
            <p className="text-sm text-text-tertiary">No scans yet. Run a Fuel Scan to build your history.</p>
          ) : (
            <div className="space-y-2">
              {scans.map((scan) => (
                <div key={scan.id} className="flex flex-col gap-3 rounded-lg border border-border bg-bg-secondary p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-medium">{scan.product_name || 'Scan'}</p>
                    <p className="text-xs text-text-tertiary">{new Date(scan.created_at).toLocaleDateString()}</p>
                  </div>
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                    scan.score >= 70 ? 'bg-accent-glow text-accent' : scan.score >= 40 ? 'bg-warning/10 text-warning' : 'bg-error/10 text-error'
                  }`}>
                    {scan.score}/100
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

        <section>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-semibold">Recent Form Sessions</h2>
            <Link href="/dashboard/workouts" className="text-sm text-accent hover:text-accent-hover">View all</Link>
          </div>
          {workouts.length === 0 ? (
            <p className="text-sm text-text-tertiary">No workout analyses yet. Upload a set to get started.</p>
          ) : (
            <div className="space-y-2">
              {workouts.map((workout) => (
                <div key={workout.id} className="flex flex-col gap-3 rounded-lg border border-border bg-bg-secondary p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-medium">{workout.exercise_type.replace(/_/g, ' ')}</p>
                    <p className="text-xs text-text-tertiary">{new Date(workout.created_at).toLocaleDateString()}</p>
                  </div>
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                    workout.form_score >= 70 ? 'bg-accent-glow text-accent' : workout.form_score >= 40 ? 'bg-warning/10 text-warning' : 'bg-error/10 text-error'
                  }`}>
                    {workout.form_score}/100
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
