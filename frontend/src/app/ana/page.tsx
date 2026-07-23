'use client';

import { useState, useRef, useEffect } from 'react';
import { askCoach } from '@/lib/gradio';
import type { ChatMessage as ChatMsg } from '@/lib/types';
import ChatMessage from '@/components/ana/ChatMessage';
import ChatInput from '@/components/ana/ChatInput';
import ChatSuggestions from '@/components/ana/ChatSuggestions';

export default function AnaPage() {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  async function sendMessage(text?: string) {
    const msg = (text || input).trim();
    if (!msg || sending) return;
    setInput('');

    const userMsg: ChatMsg = { role: 'user', content: msg };
    const updated = [...messages, userMsg];
    setMessages(updated);
    setSending(true);

    try {
      const reply = await askCoach(msg);
      setMessages((prev) => [...prev, { role: 'assistant', content: reply }]);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Sorry, something went wrong: ${message}` },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-[calc(100dvh-120px)] max-w-3xl flex-col px-4 py-4 sm:px-6 md:h-[calc(100vh-130px)]">
      <div className="flex items-center gap-3 border-b border-border pb-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-accent to-accent-hover">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446A9 9 0 1 1 12 3z" />
          </svg>
        </div>
        <div>
          <h1 className="font-display text-lg font-bold">AI Fit Pro Coach</h1>
          <p className="text-xs text-text-tertiary">Nutrition and recovery assistant</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto py-6">
        {messages.length === 0 ? (
          <ChatSuggestions onSelect={(text) => sendMessage(text)} />
        ) : (
          <div className="space-y-4">
            {messages.map((message, index) => (
              <ChatMessage key={index} role={message.role} content={message.content} />
            ))}
            {sending && (
              <div className="flex justify-start">
                <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-md bg-bg-tertiary px-5 py-3">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-text-tertiary [animation-delay:0ms]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-text-tertiary [animation-delay:150ms]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-text-tertiary [animation-delay:300ms]" />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="border-t border-border pt-4">
        <ChatInput value={input} onChange={setInput} onSend={() => sendMessage()} disabled={sending} />
      </div>
    </div>
  );
}
