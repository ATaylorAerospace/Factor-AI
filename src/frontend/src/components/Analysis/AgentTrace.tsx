import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Bot } from 'lucide-react';
import { Disclaimer } from '../shared/Disclaimer';
import type { TraceEntry } from '../../types';

interface AgentTraceProps {
  trace: TraceEntry[];
}

export function AgentTrace({ trace }: AgentTraceProps) {
  const [expanded, setExpanded] = useState(false);

  if (trace.length === 0) return null;

  return (
    <div
      style={{
        background: 'white',
        borderRadius: 12,
        padding: 24,
        marginBottom: 20,
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      }}
    >
      <div
        style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
        <Bot size={20} color="#4472C4" />
        <h2 style={{ color: '#1a1a2e', margin: 0 }}>Agent Reasoning Trace ({trace.length})</h2>
      </div>

      {expanded && (
        <div style={{ marginTop: 16 }}>
          <Disclaimer />
          {trace.map((entry, i) => (
            <div
              key={i}
              style={{
                borderLeft: '3px solid #4472C4',
                paddingLeft: 16,
                marginBottom: 12,
                paddingBottom: 12,
                borderBottom: '1px solid #f0f0f0',
              }}
            >
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                <strong style={{ color: '#4472C4' }}>{entry.agent}</strong>
                <span style={{ color: '#6c757d', fontSize: '0.85em' }}>{entry.action}</span>
              </div>
              <pre
                style={{
                  background: '#f8f9fa',
                  padding: 8,
                  borderRadius: 4,
                  fontSize: '0.8em',
                  overflow: 'auto',
                  maxHeight: 200,
                }}
              >
                {JSON.stringify(entry.details, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
