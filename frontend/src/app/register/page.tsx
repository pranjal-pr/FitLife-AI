'use client';

import { useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Alert from '@/components/ui/Alert';

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    setLoading(true);
    try {
      await register(name, email, password);
      router.push('/dashboard');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-md flex-col justify-center px-6 py-16">
      <h1 className="font-display text-3xl font-bold text-center">Create your account</h1>
      <p className="mt-2 text-center text-text-secondary">Start tracking your routine with AI Fit Pro</p>

      {error && <Alert variant="error" className="mt-6">{error}</Alert>}

      <form onSubmit={handleSubmit} className="mt-8 space-y-5">
        <Input
          label="Name"
          required
          placeholder="Your name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <Input
          label="Email"
          type="email"
          required
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Input
          label="Password"
          type="password"
          required
          placeholder="Min. 8 characters"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <Button type="submit" loading={loading} className="w-full" size="lg">
          Create Account
        </Button>
      </form>

      <p className="mt-8 text-center text-sm text-text-secondary">
        Already have an account?{' '}
        <Link href="/login" className="text-accent hover:text-accent-hover">Sign in</Link>
      </p>
    </div>
  );
}
