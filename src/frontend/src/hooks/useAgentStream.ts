import { useState, useCallback, useRef } from 'react';
import type { TraceEntry } from '../types';

interface StreamState {
  isStreaming: boolean;
  events: TraceEntry[];
  error: string | null;
}

export function useAgentStream() {
  const [state, setState] = useState<StreamState>({
    isStreaming: false,
    events: [],
    error: null,
  });
  const abortRef = useRef<AbortController | null>(null);

  const startStream = useCallback(async (url: string) => {
    abortRef.current = new AbortController();

    setState({ isStreaming: true, events: [], error: null });

    try {
      const response = await fetch(url, { signal: abortRef.current.signal });
      if (!response.ok) throw new Error(`Stream failed: ${response.statusText}`);

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const block of lines) {
          const eventMatch = block.match(/^event:\s*(.+)$/m);
          const dataMatch = block.match(/^data:\s*(.+)$/m);

          if (eventMatch && dataMatch) {
            try {
              const data = JSON.parse(dataMatch[1]);
              setState((prev) => ({
                ...prev,
                events: [
                  ...prev.events,
                  {
                    agent: data.agent || 'system',
                    action: eventMatch[1],
                    timestamp: Date.now(),
                    details: data,
                  },
                ],
              }));
            } catch {
              // skip malformed events
            }
          }
        }
      }

      setState((prev) => ({ ...prev, isStreaming: false }));
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          error: err instanceof Error ? err.message : 'Stream error',
        }));
      }
    }
  }, []);

  const stopStream = useCallback(() => {
    abortRef.current?.abort();
    setState((prev) => ({ ...prev, isStreaming: false }));
  }, []);

  return { ...state, startStream, stopStream };
}
