import { stackHighlights } from '@/lib/site';

const endpoints = [
  { method: 'GET', path: '/health', desc: 'Gateway health check' },
  { method: 'GET', path: '/api/v1/health', desc: 'API health check' },
  { method: 'POST', path: '/api/v1/auth/register', desc: 'Create a new account' },
  { method: 'POST', path: '/api/v1/auth/login', desc: 'Get JWT tokens' },
  { method: 'POST', path: '/api/v1/auth/refresh', desc: 'Refresh access token' },
  { method: 'GET', path: '/api/v1/user', desc: 'Get current user profile' },
  { method: 'PUT', path: '/api/v1/user/settings', desc: 'Update user settings' },
  { method: 'DELETE', path: '/api/v1/user', desc: 'Delete the signed-in account' },
  { method: 'GET', path: '/api/v1/user/scans', desc: 'Load saved nutrition scan history' },
  { method: 'GET', path: '/api/v1/user/workouts', desc: 'Load saved workout history' },
  { method: 'GET', path: '/api/v1/dashboard/stats', desc: 'Dashboard statistics' },
  { method: 'POST', path: '/api/v1/nutri-ai/upload', desc: 'Upload nutrition label image' },
  { method: 'POST', path: '/api/v1/nutri-ai/analyze', desc: 'Analyze nutrition data' },
  { method: 'GET', path: '/api/v1/muscle-ai/exercises', desc: 'List supported workout types' },
  { method: 'POST', path: '/api/v1/muscle-ai/upload', desc: 'Upload workout video' },
  { method: 'GET', path: '/api/v1/muscle-ai/task/:id', desc: 'Poll workout task status' },
  { method: 'POST', path: '/api/v1/ana/chat', desc: 'Chat with AI Fit Pro Coach' },
];

export default function DevelopersPage() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-24">
      <div className="mb-16 text-center">
        <span className="mb-4 inline-block rounded-full border border-accent/30 bg-accent-glow px-3 py-1 text-xs font-semibold text-accent">Build</span>
        <h1 className="font-display text-4xl font-bold">AI Fit Pro Architecture</h1>
        <p className="mx-auto mt-4 max-w-2xl text-text-secondary">
          AI Fit Pro uses a product-style architecture: a Next.js frontend, Flask gateway, AI services, and a shared data layer that keeps nutrition, workouts, and coaching connected.
        </p>
      </div>

      <section className="mb-16">
        <h2 className="mb-6 font-display text-2xl font-bold">Stack</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {stackHighlights.map((item) => (
            <div key={item} className="rounded-xl border border-border bg-bg-secondary px-5 py-4 text-sm text-text-secondary">
              {item}
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-2 font-display text-2xl font-bold">Current API Routes</h2>
        <p className="mb-6 max-w-3xl text-sm leading-relaxed text-text-secondary">
          These are the main live routes exposed by the AI Fit Pro gateway and used by the frontend for auth, profile persistence, nutrition scoring, workout analysis, and coach chat.
        </p>
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead className="bg-bg-secondary text-left text-text-tertiary">
              <tr>
                <th className="px-6 py-3 font-medium">Method</th>
                <th className="px-6 py-3 font-medium">Endpoint</th>
                <th className="hidden px-6 py-3 font-medium sm:table-cell">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {endpoints.map((endpoint) => (
                <tr key={endpoint.path} className="hover:bg-bg-tertiary/50">
                  <td className="px-6 py-3">
                    <span className={`rounded px-2 py-0.5 font-mono text-xs font-bold ${
                      endpoint.method === 'GET'
                        ? 'bg-info/10 text-info'
                        : endpoint.method === 'PUT'
                          ? 'bg-warning/10 text-warning'
                          : endpoint.method === 'DELETE'
                            ? 'bg-error/10 text-error'
                            : 'bg-accent-glow text-accent'
                    }`}>
                      {endpoint.method}
                    </span>
                  </td>
                  <td className="px-6 py-3 font-mono text-xs">{endpoint.path}</td>
                  <td className="hidden px-6 py-3 text-text-secondary sm:table-cell">{endpoint.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

    </div>
  );
}
