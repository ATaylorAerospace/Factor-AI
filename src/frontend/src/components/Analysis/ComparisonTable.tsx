import React from 'react';
import { GitCompare } from 'lucide-react';

interface ComparisonTableProps {
  comparisons: Record<string, unknown>[];
}

const riskColors: Record<string, string> = {
  critical: '#dc3545',
  high: '#fd7e14',
  medium: '#b7791f',
  low: '#28a745',
};

export function ComparisonTable({ comparisons }: ComparisonTableProps) {
  const withFindings = comparisons.filter(
    (c) => ((c.inconsistencies as string[]) || []).length > 0
  );
  if (withFindings.length === 0) return null;

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
        <GitCompare size={20} color="#4472C4" />
        <h2 style={{ color: '#1a1a2e', margin: 0 }}>
          Cross-Document Inconsistencies ({withFindings.length})
        </h2>
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={thStyle}>Provision</th>
            <th style={thStyle}>Risk</th>
            <th style={thStyle}>Documents</th>
            <th style={thStyle}>Findings</th>
          </tr>
        </thead>
        <tbody>
          {withFindings.map((c, i) => {
            const risk = (c.risk_level as string) || 'low';
            const documents =
              (c.document_names as string[]) || (c.documents_compared as string[]) || [];
            return (
              <tr key={i}>
                <td style={tdStyle}>{((c.provision_type as string) || '').replace(/_/g, ' ')}</td>
                <td style={tdStyle}>
                  <span
                    style={{
                      color: riskColors[risk],
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      fontSize: '0.85em',
                    }}
                  >
                    {risk}
                  </span>
                </td>
                <td style={tdStyle}>{documents.join(', ')}</td>
                <td style={tdStyle}>
                  <ul style={{ margin: 0, paddingLeft: 18 }}>
                    {(c.inconsistencies as string[]).map((msg, j) => (
                      <li key={j}>{msg}</li>
                    ))}
                  </ul>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
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
  verticalAlign: 'top',
};
