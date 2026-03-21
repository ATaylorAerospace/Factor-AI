import React, { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { DropZone } from './components/Upload/DropZone';
import { BatchProgress } from './components/Upload/BatchProgress';
import { Dashboard } from './components/Analysis/Dashboard';
import { ReportViewer } from './components/Report/ReportViewer';
import { Disclaimer } from './components/shared/Disclaimer';
import { useAnalysis } from './hooks/useAnalysis';
import type { AnalysisState } from './types';

function HomePage() {
  const { state, startAnalysis } = useAnalysis();

  return (
    <div style={{ minHeight: '100vh', background: '#f8f9fa' }}>
      <header style={{
        background: 'linear-gradient(135deg, #1a1a2e, #16213e)',
        color: 'white', padding: '24px 40px',
      }}>
        <h1 style={{ fontSize: '1.8em', margin: 0 }}>
          ⚖️ Factor — Agentic AI Legal Due Diligence
        </h1>
        <p style={{ opacity: 0.7, marginTop: 4 }}>
          Autonomous agents for batch contract analysis
        </p>
      </header>

      <main style={{ maxWidth: 1200, margin: '0 auto', padding: 24 }}>
        <Disclaimer />

        {state.status === 'idle' && (
          <DropZone onFilesSelected={startAnalysis} />
        )}

        {state.status === 'uploading' && (
          <BatchProgress files={state.files} progress={state.progress} />
        )}

        {(state.status === 'analyzing' || state.status === 'complete') && state.report && (
          <Dashboard report={state.report} trace={state.trace} />
        )}
      </main>

      <footer style={{ textAlign: 'center', padding: 20, color: '#6c757d', fontSize: '0.85em' }}>
        <p>Factor by A Taylor | Dataset: Taylor658/synthetic-legal (ALL content is synthetic)</p>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/report/:sessionId" element={<ReportViewer />} />
    </Routes>
  );
}
