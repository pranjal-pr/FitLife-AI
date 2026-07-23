'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { createPortal } from 'react-dom';
import type { User } from '@/lib/types';
import { site } from '@/lib/site';
import { getTokens } from '@/lib/api';
import ThemeToggle from './ThemeToggle';

interface Props {
  open: boolean;
  onClose: () => void;
  links: { href: string; label: string }[];
  user: User | null;
  loading?: boolean;
  onLogout: () => void;
}

export default function MobileMenu({ open, onClose, links, user, loading = false, onLogout }: Props) {
  const panelRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);
  const shouldShowLoadingState = useMemo(() => {
    if (!mounted) return loading;
    const params = new URLSearchParams(window.location.search);
    const { access, refresh } = getTokens();
    return loading && (!!access || !!refresh || (params.has('access_token') && params.has('refresh_token')));
  }, [loading, mounted]);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    document.body.style.overflow = 'hidden';
    panelRef.current?.querySelector('a')?.focus();
    return () => {
      document.removeEventListener('keydown', handler);
      document.body.style.overflow = '';
    };
  }, [open, onClose]);

  if (!open || !mounted) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 bg-bg-primary md:hidden">
      <div className="absolute inset-0 bg-bg-primary" onClick={onClose} />
      <div
        ref={panelRef}
        className="absolute inset-0 flex h-full w-full flex-col bg-bg-primary animate-in fade-in slide-in-from-right"
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-center justify-between border-b border-border px-5 pb-4 pt-6 sm:px-6">
          <span className="font-display text-lg font-bold">{site.name}</span>
          <button
            onClick={onClose}
            className="rounded-xl border border-border bg-bg-secondary p-3 text-text-secondary transition-colors hover:border-border-hover hover:bg-bg-elevated hover:text-text-primary"
            aria-label="Close menu"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-5 py-5 sm:px-6">
          <ul className="space-y-3">
            {links.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  onClick={onClose}
                  className="block rounded-2xl border border-border bg-bg-secondary px-4 py-4 text-lg font-medium text-text-primary transition-colors hover:border-border-hover hover:bg-bg-elevated"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div className="space-y-3 border-t border-border px-5 py-5 pb-8 sm:px-6">
          <a
            href={site.backend.appUrl}
            target="_blank"
            rel="noreferrer"
            className="block w-full rounded-2xl border border-border bg-bg-secondary px-4 py-4 text-center text-base text-text-primary hover:bg-bg-elevated"
          >
            Backend
          </a>
          <ThemeToggle className="w-full justify-center rounded-2xl bg-bg-secondary py-4 text-base text-text-primary" />
          {shouldShowLoadingState ? (
            <div className="h-12 animate-pulse rounded-lg border border-border bg-bg-tertiary" />
          ) : user ? (
            <>
              <Link
                href="/dashboard"
                onClick={onClose}
                className="block w-full rounded-2xl bg-accent px-4 py-4 text-center text-base font-medium text-white hover:bg-accent-hover"
              >
                Open Dashboard
              </Link>
              <button
                onClick={() => {
                  onLogout();
                  onClose();
                }}
                className="block w-full rounded-2xl border border-border bg-bg-secondary px-4 py-4 text-center text-base text-text-primary"
              >
                Sign Out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                onClick={onClose}
                className="block w-full rounded-2xl bg-bg-secondary px-4 py-4 text-center text-base text-text-primary hover:bg-bg-elevated"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                onClick={onClose}
                className="block w-full rounded-2xl bg-accent px-4 py-4 text-center text-base font-medium text-white hover:bg-accent-hover"
              >
                Get Started
              </Link>
            </>
          )}
        </div>
      </div>
    </div>,
    document.body,
  );
}
