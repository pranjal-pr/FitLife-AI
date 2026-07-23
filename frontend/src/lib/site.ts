const backendAppUrl = (
  process.env.NEXT_PUBLIC_HF_SPACE_URL ||
  'https://praanjalpradhan-ai-fit-pro.hf.space'
).replace(/\/$/, '');

export const site = {
  name: 'FitLife',
  title: 'FitLife - AI Fitness and Nutrition Coach',
  description:
    'FitLife is a full-stack wellness app that combines OCR nutrition scans, pose-based workout feedback, and an AI coach into one daily training workflow.',
  contactEmail: process.env.NEXT_PUBLIC_CONTACT_EMAIL || 'hello@example.com',
  backend: {
    appUrl: backendAppUrl,
    settingsUrl: process.env.NEXT_PUBLIC_BACKEND_SETTINGS_URL || '',
  },
};

export const navLinks = [
  { href: '/nutri-ai', label: 'Fuel Scan' },
  { href: '/muscle-ai', label: 'Form Coach' },
  { href: '/ana', label: 'FitLife Coach' },
  { href: '/pricing', label: 'Plans' },
];

export const products = [
  {
    href: '/nutri-ai',
    badge: 'OCR + scoring',
    title: 'Fuel Scan',
    desc: 'Scan packaged food labels, surface the macro tradeoffs, and get recommendations matched to your goal.',
  },
  {
    href: '/muscle-ai',
    badge: 'Pose analysis',
    title: 'Form Coach',
    desc: 'Upload a lifting clip and get rep counts, posture cues, and injury-risk feedback in one workflow.',
  },
  {
    href: '/ana',
    badge: 'Nutrition-aware coach',
    title: 'FitLife Coach',
    desc: 'Ask for meal ideas, recovery suggestions, and ingredient swaps from a nutrition-aware AI assistant.',
  },
];

export const stackHighlights = [
  'Next.js 15 + React 19 frontend',
  'Flask API gateway with JWT auth',
  'OCR label extraction pipeline',
  'YOLOv8-based workout analysis',
  'Knowledge-grounded meal coach with chat history',
  'Dashboard flows for scans and workouts',
];
