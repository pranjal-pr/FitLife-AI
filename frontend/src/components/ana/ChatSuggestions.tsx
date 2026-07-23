'use client';

const suggestions = [
  'Build a high-protein vegetarian dinner with lentils and paneer.',
  'I trained legs today. What should I eat for recovery?',
  'Suggest three breakfast ideas under 500 calories.',
  'I have eggs, oats, spinach, and bananas. What can I make?',
];

interface Props {
  onSelect: (text: string) => void;
}

export default function ChatSuggestions({ onSelect }: Props) {
  return (
    <div className="flex flex-col items-center gap-4 py-8">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-accent to-accent-hover shadow-lg shadow-accent/15">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446A9 9 0 1 1 12 3z" />
        </svg>
      </div>
      <h2 className="font-display text-xl font-bold">Chat with AI Fit Pro Coach</h2>
      <p className="max-w-md text-center text-sm text-text-secondary">
        Ask for meal ideas, ingredient swaps, recovery meals, or a simple nutrition plan around your training week.
      </p>
      <div className="mt-4 flex flex-wrap justify-center gap-2">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            onClick={() => onSelect(suggestion)}
            className="rounded-full border border-border bg-bg-secondary px-4 py-2 text-xs text-text-secondary transition-colors hover:border-accent/40 hover:text-text-primary"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}
