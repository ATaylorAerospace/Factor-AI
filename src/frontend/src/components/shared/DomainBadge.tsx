import React from 'react';

interface DomainBadgeProps {
  domain: string;
  isDueDiligence?: boolean;
}

const DOMAIN_COLORS: Record<string, string> = {
  'Contract Law & UCC Analysis': '#4472C4',
  'Corporate/Commercial Law': '#2E86AB',
  'Intellectual Property': '#A23B72',
  'Tax Law': '#F18F01',
  'Environmental Law': '#28a745',
  'Administrative Law': '#6c757d',
  'Tort Law': '#dc3545',
  'Constitutional Law': '#6f42c1',
  'Criminal Law & Procedure': '#343a40',
  'International Law': '#17a2b8',
  'Civil Procedure': '#20c997',
  'Immigration Law': '#e83e8c',
  'Family Law': '#fd7e14',
};

export function DomainBadge({ domain, isDueDiligence }: DomainBadgeProps) {
  const color = DOMAIN_COLORS[domain] || '#6c757d';

  return (
    <span
      style={{
        display: 'inline-block',
        background: `${color}20`,
        color,
        border: `1px solid ${color}40`,
        padding: '2px 10px',
        borderRadius: 12,
        fontSize: '0.8em',
        fontWeight: 600,
      }}
    >
      {domain}
      {isDueDiligence && ' (DD)'}
    </span>
  );
}
