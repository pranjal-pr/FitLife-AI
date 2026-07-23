import Link from 'next/link';

const features = [
  { title: 'Studio Dashboards', desc: 'Centralize member check-ins, scan activity, and workout feedback for coaching teams.' },
  { title: 'Dedicated Infrastructure', desc: 'Spin up isolated environments for gyms, wellness programs, or internal pilots.' },
  { title: 'SSO and Compliance', desc: 'Support team onboarding, access controls, and production-style deployment requirements.' },
  { title: 'Priority Support', desc: 'Use AI Fit Pro as a white-glove pilot with faster issue triage and roadmap feedback loops.' },
  { title: 'White-Label Launches', desc: 'Adapt the app for coach brands, gym memberships, or internal health initiatives.' },
  { title: 'Unlimited API Access', desc: 'Plug nutrition and form analysis into broader products without demo-tier limits.' },
];

export default function EnterprisePage() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-24">
      <div className="mb-16 text-center">
        <h1 className="font-display text-4xl font-bold">AI Fit Pro for coaches, gyms, and teams</h1>
        <p className="mx-auto mt-4 max-w-2xl text-text-secondary">
          The same product surface can be adapted for team rollouts, wellness programs, and white-label pilots.
        </p>
      </div>

      <div className="mb-16 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {features.map((feature) => (
          <div key={feature.title} className="rounded-xl border border-border bg-bg-secondary p-8">
            <h3 className="mb-2 font-semibold">{feature.title}</h3>
            <p className="text-sm text-text-secondary">{feature.desc}</p>
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-border bg-bg-secondary p-12 text-center">
        <h2 className="font-display text-2xl font-bold">Ready to get started?</h2>
        <p className="mt-3 text-text-secondary">Talk through the product, the stack, and the rollout model that fits your use case.</p>
        <Link href="/contact" className="mt-6 inline-block rounded-lg bg-accent px-8 py-3 text-sm font-medium text-white shadow-md shadow-accent/20 hover:bg-accent-hover">
          Start a Conversation
        </Link>
      </div>
    </div>
  );
}
