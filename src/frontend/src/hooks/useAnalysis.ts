import { useState, useCallback } from 'react';
import { uploadAndAnalyze } from '../api/client';
import type { AnalysisStage, AnalysisState, Report, SkippedDocument } from '../types';

const initialState: AnalysisState = {
  status: 'idle',
  files: [],
  progress: 0,
  stage: null,
  skipped: [],
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

    let gotReport = false;
    let failed = false;

    const fail = (message: string) => {
      failed = true;
      setState((prev) => ({ ...prev, status: 'error', error: message }));
    };

    try {
      await uploadAndAnalyze(files, (event) => {
        const data = event.data as Record<string, unknown>;

        switch (event.type) {
          case 'session':
            setState((prev) => ({
              ...prev,
              sessionId: data.session_id as string,
              status: 'analyzing',
            }));
            break;

          case 'status':
            setState((prev) => ({
              ...prev,
              stage: data.stage as AnalysisStage,
              progress: 0,
              trace: [
                ...prev.trace,
                {
                  agent: 'coordinator',
                  action: data.stage as string,
                  timestamp: Date.now(),
                  details: data,
                },
              ],
            }));
            break;

          case 'progress':
            setState((prev) => ({ ...prev, progress: prev.progress + 1 }));
            break;

          case 'document_skipped':
            setState((prev) => ({
              ...prev,
              progress: prev.progress + 1,
              skipped: [...prev.skipped, data as unknown as SkippedDocument],
            }));
            break;

          case 'report':
            gotReport = true;
            setState((prev) => ({
              ...prev,
              report: data as unknown as Report,
              status: 'complete',
            }));
            break;

          case 'guardrail_halt':
            fail(`Analysis halted by the cost guardrail: ${(data.message as string) || 'limit reached'}`);
            break;

          case 'error':
            fail((data.message as string) || 'Analysis failed');
            break;
        }
      });

      if (!gotReport && !failed) {
        fail('The analysis ended before a report was produced. Please try again.');
      }
    } catch (err) {
      fail(err instanceof Error ? err.message : 'Analysis failed');
    }
  }, []);

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  return { state, startAnalysis, reset };
}
