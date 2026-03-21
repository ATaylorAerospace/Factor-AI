import React from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getReport } from '../../api/client';
import { Dashboard } from '../Analysis/Dashboard';
import { ExportButton } from './ExportButton';
import { Disclaimer } from '../shared/Disclaimer';

export function ReportViewer() {
  const { sessionId } = useParams<{ sessionId: string }>();

  const { data: report, isLoading, error } = useQuery({
    queryKey: ['report', sessionId],
    queryFn: () => getReport(sessionId!),
    enabled: !!sessionId,
  });

  if (isLoading) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <p>Loading report...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: '#dc3545' }}>
        <p>Failed to load report: {error instanceof Error ? error.message : 'Not found'}</p>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f8f9fa' }}>
      <header
        style={{
          background: 'linear-gradient(135deg, #1a1a2e, #16213e)',
          color: 'white',
          padding: '24px 40px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <h1 style={{ fontSize: '1.5em', margin: 0 }}>
            ⚖️ Factor — Due Diligence Report
          </h1>
          <p style={{ opacity: 0.7, marginTop: 4 }}>Session: {sessionId}</p>
        </div>
        <ExportButton sessionId={sessionId!} />
      </header>

      <main style={{ maxWidth: 1200, margin: '0 auto', padding: 24 }}>
        <Disclaimer />
        <Dashboard report={report} trace={[]} />
      </main>
    </div>
  );
}
