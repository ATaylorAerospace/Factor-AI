import React from 'react';
import { AlertTriangle, CheckCircle, AlertCircle, XCircle } from 'lucide-react';

interface ProvisionCardProps {
  provision: Record<string, unknown>;
}

const riskIcons: Record<string, React.ReactNode> = {
  critical: <XCircle size={20} color="#dc3545" />,
  high: <AlertCircle size={20} color="#fd7e14" />,
  medium: <AlertTriangle size={20} color="#ffc107" />,
  low: <CheckCircle size={20} color="#28a745" />,
};

const riskColors: Record<string, string> = {
  critical: '#fff5f5',
  high: '#fff8f0',
  medium: '#fffef0',
  low: '#f0fff4',
};

export function ProvisionCard({ provision }: ProvisionCardProps) {
  const riskLevel = (provision.risk_level as string) || 'low';
  const factors = (provision.factors as string[]) || [];
  const provisionType = ((provision.provision_type as string) || '').replace(/_/g, ' ');
  const documentName = provision.document as string | undefined;
  const excerpt = provision.excerpt as string | undefined;

  return (
    <div
      style={{
        background: riskColors[riskLevel] || '#f8f9fa',
        border: '1px solid #e9ecef',
        borderRadius: 8,
        padding: 16,
        marginBottom: 12,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        {riskIcons[riskLevel]}
        <div style={{ flex: 1 }}>
          <strong style={{ textTransform: 'capitalize' }}>{provisionType || 'Provision'}</strong>
          {documentName && (
            <span style={{ color: '#6c757d', fontSize: '0.85em', marginLeft: 8 }}>
              {documentName}
            </span>
          )}
        </div>
        <span
          style={{
            textTransform: 'uppercase',
            fontSize: '0.8em',
            fontWeight: 700,
            color: riskLevel === 'low' ? '#28a745' : riskLevel === 'critical' ? '#dc3545' : '#fd7e14',
          }}
        >
          {riskLevel} — {String(provision.score || 0)}/10
        </span>
      </div>

      {excerpt && (
        <blockquote
          style={{
            margin: '4px 0 8px',
            padding: '6px 10px',
            borderLeft: '3px solid #dee2e6',
            color: '#333',
            fontSize: '0.85em',
            fontStyle: 'italic',
          }}
        >
          {excerpt}
        </blockquote>
      )}

      <p style={{ color: '#555', fontSize: '0.9em', margin: '4px 0' }}>
        {provision.explanation as string}
      </p>

      {factors.length > 0 && (
        <div style={{ marginTop: 8 }}>
          {factors.map((f, i) => (
            <span
              key={i}
              style={{
                display: 'inline-block',
                background: '#e2e3e5',
                color: '#383d41',
                padding: '2px 8px',
                borderRadius: 4,
                fontSize: '0.75em',
                marginRight: 4,
                marginBottom: 4,
              }}
            >
              {f}
            </span>
          ))}
        </div>
      )}

      {Boolean(provision.is_synthetic) && (
        <span
          style={{
            display: 'inline-block',
            background: '#fff3cd',
            color: '#856404',
            padding: '2px 8px',
            borderRadius: 4,
            fontSize: '0.7em',
            marginTop: 8,
          }}
        >
          SYNTHETIC DATA
        </span>
      )}
    </div>
  );
}
