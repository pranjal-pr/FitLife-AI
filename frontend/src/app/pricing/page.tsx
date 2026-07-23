import Link from 'next/link';

const plans = [
  {
    name: 'Starter',
    price: '$0',
    period: 'forever',
    features: ['5 label scans / month', '2 workout analyses / month', 'AI Fit Pro Coach access', 'Basic dashboard insights'],
    cta: 'Start Free',
    href: '/register',
    accent: false,
  },
  {
    name: 'Momentum',
    price: '$12',
    period: '/month',
    features: ['Unlimited label scans', 'Unlimited form analyses', 'Priority coach responses', 'Advanced progress analytics', 'Exportable reports', 'API access (1K calls/month)'],
    cta: 'Choose Momentum',
    href: '/register',
    accent: true,
  },
  {
    name: 'Team',
    price: 'Custom',
    period: '',
    features: ['Everything in Momentum', 'Dedicated environments', 'Coach and gym onboarding', 'SSO and compliance', 'Priority support SLA', 'Unlimited API access'],
    cta: 'Talk to Us',
    href: '/enterprise',
    accent: false,
  },
];

export default function PricingPage() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-24">
      <div className="mb-16 text-center">
        <h1 className="font-display text-4xl font-bold">Plans that match how seriously you train</h1>
        <p className="mx-auto mt-4 max-w-2xl text-text-secondary">
          Start with the demo-friendly tier, then scale into deeper tracking, coaching, and team deployment.
        </p>
      </div>
      <div className="grid gap-8 md:grid-cols-3">
        {plans.map((plan) => (
          <div
            key={plan.name}
            className={`flex flex-col rounded-2xl border p-8 ${
              plan.accent ? 'border-accent/40 bg-bg-secondary shadow-xl shadow-accent/5' : 'border-border bg-bg-secondary'
            }`}
          >
            {plan.accent && (
              <span className="mb-4 inline-block w-fit rounded-full border border-accent/30 bg-accent-glow px-3 py-1 text-xs font-semibold text-accent">
                MOST COMPLETE
              </span>
            )}
            <h2 className="text-xl font-bold">{plan.name}</h2>
            <div className="mt-4 flex items-baseline gap-1">
              <span className="text-4xl font-bold">{plan.price}</span>
              {plan.period && <span className="text-text-tertiary">{plan.period}</span>}
            </div>
            <ul className="mt-8 flex-1 space-y-3">
              {plan.features.map((feature) => (
                <li key={feature} className="flex items-center gap-2 text-sm text-text-secondary">
                  <svg className="h-4 w-4 shrink-0 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  {feature}
                </li>
              ))}
            </ul>
            <Link
              href={plan.href}
              className={`mt-8 block rounded-lg py-3 text-center text-sm font-medium transition-colors ${
                plan.accent
                  ? 'bg-accent text-white shadow-md shadow-accent/20 hover:bg-accent-hover'
                  : 'border border-border text-text-secondary hover:border-border-hover hover:text-text-primary'
              }`}
            >
              {plan.cta}
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
