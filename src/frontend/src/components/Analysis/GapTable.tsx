import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface GapTableProps {
  gaps: Record<string, unknown>[];
}

const severityColors: Record<string, string> = {
  critical: '#dc3545',
  high: '#fd7e14',
  medium: '#ffc107',
  low: '#28a745',
};

export function GapTable({ gaps }: GapTableProps) {
  if (gaps.length === 0) return null;

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
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <AlertTriangle size={20} color="#fd7e14" />
        <h2 style={{ color: '#1a1a2e', margin: 0 }}>Missing Provisions ({gaps.length})</h2>
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={thStyle}>Missing Provision</th>
            <th style={thStyle}>Severity</th>
            <th style={thStyle}>Recommendation</th>
          </tr>
        </thead>
        <tbody>
          {gaps.map((gap, i) => (
            <tr key={i}>
              <td style={tdStyle}>
                {((gap.missing_provision as string) || '').replace(/_/g, ' ')}
              </td>
              <td style={tdStyle}>
                <span
                  style={{
                    color: severityColors[(gap.severity as string) || 'medium'],
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    fontSize: '0.85em',
                  }}
                >
                  {(gap.severity as string) || 'medium'}
                </span>
              </td>
              <td style={tdStyle}>{gap.recommendation as string}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <p
        style={{
          marginTop: 12,
          fontSize: '0.8em',
          color: '#856404',
          background: '#fff3cd',
          padding: '8px 12px',
          borderRadius: 4,
        }}
      >
        SYNTHETIC DATA: Gap analysis references synthetic checklists. Not legal advice.
      </p>
    </div>
  );
}

const thStyle: React.CSSProperties = {
  background: '#4472C4',
  color: 'white',
  padding: '10px 12px',
  textAlign: 'left',
  fontSize: '0.9em',
};

const tdStyle: React.CSSProperties = {
  padding: '10px 12px',
  borderBottom: '1px solid #e9ecef',
  fontSize: '0.9em',
};
