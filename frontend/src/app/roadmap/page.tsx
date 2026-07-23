const timeline = [
  {
    quarter: 'Q1 2026',
    status: 'completed',
    items: [
      'AI Fit Pro brand system and landing experience',
      'Fuel Scan OCR workflow',
      'JWT authentication and user dashboard',
      'Async workout analysis pipeline',
    ],
  },
  {
    quarter: 'Q2 2026',
    status: 'in-progress',
    items: [
      'Mobile-first polish and PWA support',
      'Multi-language nutrition labels',
      'Exercise-specific coaching cues',
      'Barcode scanner support',
    ],
  },
  {
    quarter: 'Q3 2026',
    status: 'planned',
    items: [
      'Meal planning calendar',
      'Wearable integrations',
      'Longitudinal progress insights',
      'PostgreSQL production migration',
    ],
  },
  {
    quarter: 'Q4 2026',
    status: 'planned',
    items: [
      'Coach and gym white-label mode',
      'Advanced analytics workspace',
      'Custom model tuning for teams',
      'React Native companion app',
    ],
  },
];

const statusStyles: Record<string, string> = {
  completed: 'bg-accent-glow text-accent border-accent/30',
  'in-progress': 'bg-info/10 text-info border-info/30',
  planned: 'bg-bg-tertiary text-text-secondary border-border',
};

const statusLabels: Record<string, string> = {
  completed: 'Completed',
  'in-progress': 'In Progress',
  planned: 'Planned',
};

export default function RoadmapPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-24">
      <div className="mb-16 text-center">
        <h1 className="font-display text-4xl font-bold">Product Roadmap</h1>
        <p className="mx-auto mt-4 max-w-2xl text-text-secondary">
          The roadmap focuses on turning a strong demo app into a more complete coaching platform.
        </p>
      </div>

      <div className="space-y-8">
        {timeline.map((entry) => (
          <div key={entry.quarter} className="rounded-xl border border-border bg-bg-secondary p-8">
            <div className="mb-4 flex items-center gap-3">
              <h2 className="font-display text-xl font-bold">{entry.quarter}</h2>
              <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${statusStyles[entry.status]}`}>
                {statusLabels[entry.status]}
              </span>
            </div>
            <ul className="space-y-2">
              {entry.items.map((item) => (
                <li key={item} className="flex items-center gap-3 text-sm text-text-secondary">
                  {entry.status === 'completed' ? (
                    <svg className="h-4 w-4 shrink-0 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  ) : (
                    <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-text-tertiary" />
                  )}
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
