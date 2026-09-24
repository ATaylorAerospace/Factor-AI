import { AlertTriangle, FileWarning } from 'lucide-react';
import { ProvisionCard } from './ProvisionCard';
import { RiskHeatmap } from './RiskHeatmap';
import { GapTable } from './GapTable';
import { ComparisonTable } from './ComparisonTable';
import { AgentTrace } from './AgentTrace';
import { ExportButton } from '../Report/ExportButton';
import { Disclaimer } from '../shared/Disclaimer';
import type { Report, TraceEntry } from '../../types';

interface DashboardProps {
  report: Report;
  trace: TraceEntry[];
  sessionId?: string | null;
  onNewAnalysis?: () => void;
}

const cardStyle = {
  background: 'white',
  borderRadius: 12,
  padding: 24,
  marginBottom: 20,
  boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
};

export function Dashboard({ report, trace, sessionId, onNewAnalysis }: DashboardProps) {
  const section = (title: string) => report.sections.find((s) => s.title === title)?.items || [];
  const riskScores = section('Risk Assessment');
  const gaps = section('Gap Analysis');
  const comparisons = section('Cross-Document Comparison');
  const skipped = report.skipped_documents || [];

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
      <div style={cardStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
          <h2 style={{ color: '#1a1a2e', margin: 0, flex: 1 }}>Executive Summary</h2>
          {sessionId && <ExportButton sessionId={sessionId} />}
          {onNewAnalysis && (
            <button
              onClick={onNewAnalysis}
              style={{
                padding: '8px 16px',
                background: 'white',
                color: '#4472C4',
                border: '1px solid #4472C4',
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: '0.9em',
              }}
            >
              New analysis
            </button>
          )}
        </div>
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

      {/* Documents that could not be analyzed */}
      {skipped.length > 0 && (
        <div style={{ ...cardStyle, background: '#fff8e1', border: '1px solid #ffe08a' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <FileWarning size={20} color="#b7791f" />
            <h2 style={{ color: '#1a1a2e', margin: 0 }}>Not analyzed ({skipped.length})</h2>
          </div>
          {skipped.map((doc) => (
            <p key={doc.document_id} style={{ margin: '6px 0', color: '#333' }}>
              <strong>{doc.document}</strong> — {doc.reason}
            </p>
          ))}
        </div>
      )}

      {/* Risk Heatmap */}
      <RiskHeatmap riskScores={riskScores as Record<string, unknown>[]} />

      {/* Provision Cards */}
      <div style={cardStyle}>
        <h2 style={{ color: '#1a1a2e', marginBottom: 16 }}>Risk Assessment</h2>
        {riskScores.map((item, i) => (
          <ProvisionCard key={i} provision={item as Record<string, unknown>} />
        ))}
        {riskScores.length === 0 && (
          <p style={{ color: '#6c757d', display: 'flex', alignItems: 'center', gap: 6 }}>
            <AlertTriangle size={16} /> No risk scores available.
          </p>
        )}
      </div>

      {/* Gap Table */}
      <GapTable gaps={gaps as Record<string, unknown>[]} />

      {/* Cross-document comparison */}
      <ComparisonTable comparisons={comparisons as Record<string, unknown>[]} />

      {/* Agent Trace */}
      <AgentTrace trace={trace} />
    </div>
  );
}
