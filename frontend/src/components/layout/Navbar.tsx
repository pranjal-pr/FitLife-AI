'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';
import { getTokens } from '@/lib/api';
import MobileMenu from './MobileMenu';
import ThemeToggle from './ThemeToggle';
import { navLinks, site } from '@/lib/site';

export default function Navbar() {
  const { user, loading, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const shouldShowLoadingState = useMemo(() => {
    if (!mounted) return loading;
    const params = new URLSearchParams(window.location.search);
    const { access, refresh } = getTokens();
    return loading && (!!access || !!refresh || (params.has('access_token') && params.has('refresh_token')));
  }, [loading, mounted]);

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-bg-primary/80 backdrop-blur-lg">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 sm:py-4">
        <Link href="/" className="text-xl font-bold font-display tracking-tight text-text-primary">
          {site.name}
        </Link>

        <ul className="hidden items-center gap-8 md:flex">
          {navLinks.map((link) => (
            <li key={link.href}>
              <Link href={link.href} className="text-sm text-text-secondary transition-colors hover:text-text-primary">
                {link.label}
              </Link>
            </li>
          ))}
        </ul>

        <div className="hidden items-center gap-3 md:flex">
          <a
            href={site.backend.appUrl}
            target="_blank"
            rel="noreferrer"
            className="rounded-lg border border-border px-4 py-2 text-sm text-text-secondary transition-colors hover:border-border-hover hover:text-text-primary"
          >
            Backend
          </a>
          <ThemeToggle compact />
          {shouldShowLoadingState ? (
            <div className="h-10 w-36 animate-pulse rounded-lg border border-border bg-bg-secondary" />
          ) : user ? (
            <>
              <Link
                href="/dashboard"
                className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white shadow-md shadow-accent/15 transition-colors hover:bg-accent-hover"
              >
                Open Dashboard
              </Link>
              <button
                onClick={logout}
                className="rounded-lg border border-border px-4 py-2 text-sm text-text-secondary transition-colors hover:border-border-hover hover:text-text-primary"
              >
                Sign Out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="rounded-lg px-4 py-2 text-sm text-text-secondary transition-colors hover:text-text-primary"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white shadow-md shadow-accent/15 transition-colors hover:bg-accent-hover"
              >
                Get Started
              </Link>
            </>
          )}
        </div>

        <button
          className="flex flex-col items-center justify-center rounded-2xl border border-border bg-bg-secondary/90 p-3 text-text-primary shadow-sm shadow-black/5 transition-colors hover:border-border-hover hover:bg-bg-elevated md:hidden"
          onClick={() => setMobileOpen(true)}
          aria-label="Open menu"
          aria-expanded={mobileOpen}
        >
          <span className="block h-0.5 w-7 rounded-full bg-current" />
          <span className="mt-1.5 block h-0.5 w-7 rounded-full bg-current" />
          <span className="mt-1.5 block h-0.5 w-7 rounded-full bg-current" />
        </button>
      </nav>

      <MobileMenu open={mobileOpen} onClose={() => setMobileOpen(false)} links={navLinks} user={user} loading={loading} onLogout={logout} />
    </header>
  );
}
