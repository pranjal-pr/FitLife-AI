import Link from 'next/link';
import { stackHighlights } from '@/lib/site';

const experiences = [
  {
    title: 'Fuel Scan',
    desc: 'OCR-driven label reading plus profile-aware scoring for fast food decisions.',
  },
  {
    title: 'Form Coach',
    desc: 'Pose-analysis workflow that scores lifts, counts reps, and flags coaching cues.',
  },
  {
    title: 'AI Fit Pro Coach',
    desc: 'A nutrition-aware assistant grounded in curated meal and recovery guidance.',
  },
];

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-24">
      <div className="mb-16 text-center">
        <h1 className="font-display text-4xl font-bold">About AI Fit Pro</h1>
        <p className="mx-auto mt-4 max-w-2xl text-text-secondary">
          AI Fit Pro is a portfolio-first wellness product concept built to show full-stack execution, AI feature integration, and polished UX in one app.
        </p>
      </div>

      <div className="space-y-12 leading-relaxed text-text-secondary">
        <section>
          <h2 className="mb-4 font-display text-2xl font-bold text-text-primary">Product Thesis</h2>
          <p>
            Most health apps treat nutrition, training, and coaching as separate products. AI Fit Pro brings them together so a user can scan food, review lifting mechanics, and ask for meal guidance without context switching.
          </p>
        </section>

        <section>
          <h2 className="mb-4 font-display text-2xl font-bold text-text-primary">Core Experiences</h2>
          <div className="grid gap-6 md:grid-cols-3">
            {experiences.map((item) => (
              <div key={item.title} className="rounded-xl border border-border bg-bg-secondary p-6">
                <h3 className="mb-2 font-semibold text-text-primary">{item.title}</h3>
                <p className="text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-4 font-display text-2xl font-bold text-text-primary">Stack Highlights</h2>
          <div className="grid gap-3 md:grid-cols-2">
            {stackHighlights.map((item) => (
              <div key={item} className="rounded-xl border border-border bg-bg-secondary px-5 py-4 text-sm">
                {item}
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="mt-16 text-center">
        <Link href="/contact" className="rounded-lg bg-accent px-6 py-3 text-sm font-medium text-white shadow-md shadow-accent/20 hover:bg-accent-hover">
          Contact the Project
        </Link>
      </div>
    </div>
  );
}
