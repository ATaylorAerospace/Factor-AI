import axios from 'axios';
import type { Report, Session, KnowledgeResult } from '../types';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

export async function uploadAndAnalyze(
  files: File[],
  onEvent: (event: { type: string; data: unknown }) => void
): Promise<void> {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));

  const response = await fetch('/api/v1/analyze', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('No response body');

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('event:')) {
        const eventType = line.slice(6).trim();
        const nextLine = lines[lines.indexOf(line) + 1];
        if (nextLine?.startsWith('data:')) {
          try {
            const data = JSON.parse(nextLine.slice(5).trim());
            onEvent({ type: eventType, data });
          } catch {
            // skip malformed events
          }
        }
      }
    }
  }
}

export async function getSession(sessionId: string): Promise<Session> {
  const { data } = await api.get(`/sessions/${sessionId}`);
  return data;
}

export async function getReport(sessionId: string): Promise<Report> {
  const { data } = await api.get(`/reports/${sessionId}`);
  return data;
}

export async function exportReport(
  sessionId: string,
  format: 'excel' | 'html'
): Promise<{ path: string }> {
  const { data } = await api.get(`/reports/${sessionId}/export`, {
    params: { format },
  });
  return data;
}

export async function searchKnowledge(
  query: string,
  domain?: string,
  topK: number = 5
): Promise<{ results: KnowledgeResult[] }> {
  const { data } = await api.get('/knowledge/search', {
    params: { q: query, domain, top_k: topK },
  });
  return data;
}

export async function getDomains(): Promise<{
  all_domains: string[];
  due_diligence_domains: string[];
}> {
  const { data } = await api.get('/knowledge/domains');
  return data;
}

export async function healthCheck(): Promise<{ status: string; version: string }> {
  const { data } = await api.get('/health');
  return data;
}
