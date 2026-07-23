'use client';

import { useState, type FormEvent } from 'react';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Alert from '@/components/ui/Alert';

export default function ContactPage() {
  const [sent, setSent] = useState(false);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSent(true);
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-24">
      <div className="mb-12 text-center">
        <h1 className="font-display text-4xl font-bold">Contact AI Fit Pro</h1>
        <p className="mt-4 text-text-secondary">
          Use this page for feedback, feature ideas, hiring conversations, or a walkthrough request.
        </p>
      </div>

      {sent ? (
        <Alert variant="success" className="text-center">
          Thanks. Your note is in the queue and this demo confirms the form interaction end to end.
        </Alert>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid gap-6 sm:grid-cols-2">
            <Input label="Name" required placeholder="Your name" />
            <Input label="Email" type="email" required placeholder="you@example.com" />
          </div>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-text-secondary">Subject</label>
            <select className="w-full rounded-lg border border-border bg-bg-tertiary px-4 py-2.5 text-sm text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent">
              <option>General Inquiry</option>
              <option>Portfolio Review</option>
              <option>Bug Report</option>
              <option>Feature Request</option>
              <option>Team Pilot</option>
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-text-secondary">Message</label>
            <textarea
              required
              rows={5}
              placeholder="Tell us what you want to discuss..."
              className="w-full rounded-lg border border-border bg-bg-tertiary px-4 py-2.5 text-sm text-text-primary placeholder-text-tertiary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            />
          </div>
          <Button type="submit" size="lg" className="w-full">Send Message</Button>
        </form>
      )}
    </div>
  );
}
