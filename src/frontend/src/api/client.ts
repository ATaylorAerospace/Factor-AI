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
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body?.detail === 'string') detail = body.detail;
    } catch {
      // non-JSON error body; keep the status text
    }
    throw new Error(`Upload failed: ${detail}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('No response body');

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });

    // An SSE event ends with a blank line. Only complete events are parsed;
    // the unfinished tail stays buffered until the rest of it arrives, so a
    // large event (the report) split across network reads is never dropped.
    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = done ? '' : blocks.pop() ?? '';

    for (const block of blocks) {
      const event = parseSseBlock(block);
      if (event) onEvent(event);
    }

    if (done) break;
  }
}

/** Parse one SSE event block ("event: ..." plus one or more "data: ..." lines). */
export function parseSseBlock(block: string): { type: string; data: unknown } | null {
  let type = 'message';
  const dataLines: string[] = [];

  for (const line of block.split(/\r?\n/)) {
    if (line.startsWith('event:')) {
      type = line.slice(6).trim();
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).replace(/^ /, ''));
    }
  }

  if (dataLines.length === 0) return null; // comments / keep-alive pings

  try {
    return { type, data: JSON.parse(dataLines.join('\n')) };
  } catch {
    return null; // skip malformed events
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

/** Download the report file and hand it to the browser as a normal download. */
export async function exportReport(sessionId: string, format: 'excel' | 'html'): Promise<void> {
  const response = await api.get(`/reports/${sessionId}/export`, {
    params: { format },
    responseType: 'blob',
  });

  const disposition: string = response.headers['content-disposition'] ?? '';
  const match = disposition.match(/filename="?([^";]+)"?/);
  const filename = match?.[1] ?? `factor-report.${format === 'excel' ? 'xlsx' : 'html'}`;

  const url = URL.createObjectURL(response.data as Blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
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
