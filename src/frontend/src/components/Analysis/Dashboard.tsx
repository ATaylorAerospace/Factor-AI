import React from 'react';
import { ProvisionCard } from './ProvisionCard';
import { RiskHeatmap } from './RiskHeatmap';
import { GapTable } from './GapTable';
import { AgentTrace } from './AgentTrace';
import { Disclaimer } from '../shared/Disclaimer';
import type { Report, TraceEntry } from '../../types';

interface DashboardProps {
  report: Report;
  trace: TraceEntry[];
}

export function Dashboard({ report, trace }: DashboardProps) {
  const riskScores = report.sections.find((s) => s.title === 'Risk Assessment')?.items || [];
  const gaps = report.sections.find((s) => s.title === 'Gap Analysis')?.items || [];
  const comparisons =
    report.sections.find((s) => s.title === 'Cross-Document Comparison')?.items || [];

  const riskColor: Record<string, string> = {
    critical: '#dc3545',
    high: '#fd7e14',
    medium: '#ffc107',
    low: '#28a745',
  };

  return (
    <div style={{ marginTop: 24 }}>
      <Disclaimer />

      {/* Executive Summary */}
      <div
        style={{
          background: 'white',
          borderRadius: 12,
          padding: 24,
          marginBottom: 20,
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        }}
      >
        <h2 style={{ color: '#1a1a2e', marginBottom: 12 }}>Executive Summary</h2>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 12 }}>
          <span style={{ fontSize: '0.85em', color: '#6c757d' }}>Overall Risk:</span>
          <span
            style={{
              background: riskColor[report.overall_risk] || '#6c757d',
              color: report.overall_risk === 'medium' ? '#333' : 'white',
              padding: '4px 16px',
              borderRadius: 20,
              fontWeight: 700,
              textTransform: 'uppercase',
              fontSize: '0.9em',
            }}
          >
            {report.overall_risk}
          </span>
        </div>
        <p style={{ color: '#333' }}>{report.executive_summary}</p>
      </div>

      {/* Risk Heatmap */}
      <RiskHeatmap riskScores={riskScores as Record<string, unknown>[]} />

      {/* Provision Cards */}
      <div
        style={{
          background: 'white',
          borderRadius: 12,
          padding: 24,
          marginBottom: 20,
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        }}
      >
        <h2 style={{ color: '#1a1a2e', marginBottom: 16 }}>Risk Assessment</h2>
        {riskScores.map((item, i) => (
          <ProvisionCard key={i} provision={item as Record<string, unknown>} />
        ))}
        {riskScores.length === 0 && <p style={{ color: '#6c757d' }}>No risk scores available.</p>}
      </div>

      {/* Gap Table */}
      <GapTable gaps={gaps as Record<string, unknown>[]} />

      {/* Agent Trace */}
      <AgentTrace trace={trace} />
    </div>
  );
}
