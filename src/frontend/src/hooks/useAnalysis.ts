import { useState, useCallback } from 'react';
import { uploadAndAnalyze } from '../api/client';
import type { AnalysisState, Report, TraceEntry } from '../types';

const initialState: AnalysisState = {
  status: 'idle',
  files: [],
  progress: 0,
  report: null,
  trace: [],
  sessionId: null,
  error: null,
};

export function useAnalysis() {
  const [state, setState] = useState<AnalysisState>(initialState);

  const startAnalysis = useCallback(async (files: File[]) => {
    setState({
      ...initialState,
      status: 'uploading',
      files,
    });

    try {
      await uploadAndAnalyze(files, (event) => {
        switch (event.type) {
          case 'session':
            setState((prev) => ({
              ...prev,
              sessionId: (event.data as { session_id: string }).session_id,
              status: 'analyzing',
            }));
            break;

          case 'progress':
            setState((prev) => ({
              ...prev,
              progress: prev.progress + 1,
            }));
            break;

          case 'status':
            setState((prev) => ({
              ...prev,
              trace: [
                ...prev.trace,
                {
                  agent: 'coordinator',
                  action: (event.data as { stage: string }).stage,
                  timestamp: Date.now(),
                  details: event.data as Record<string, unknown>,
                },
              ],
            }));
            break;

          case 'report':
            setState((prev) => ({
              ...prev,
              report: event.data as Report,
              status: 'complete',
            }));
            break;
        }
      });
    } catch (err) {
      setState((prev) => ({
        ...prev,
        status: 'error',
        error: err instanceof Error ? err.message : 'Analysis failed',
      }));
    }
  }, []);

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  return { state, startAnalysis, reset };
}
