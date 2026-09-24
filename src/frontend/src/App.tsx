import { Routes, Route } from 'react-router-dom';
import { DropZone } from './components/Upload/DropZone';
import { BatchProgress } from './components/Upload/BatchProgress';
import { Dashboard } from './components/Analysis/Dashboard';
import { ReportViewer } from './components/Report/ReportViewer';
import { Disclaimer } from './components/shared/Disclaimer';
import { useAnalysis } from './hooks/useAnalysis';

function HomePage() {
  const { state, startAnalysis, reset } = useAnalysis();
  const inProgress =
    state.status === 'uploading' || (state.status === 'analyzing' && !state.report);

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

        {inProgress && (
          <BatchProgress files={state.files} progress={state.progress} stage={state.stage} />
        )}

        {state.status === 'error' && (
          <div
            role="alert"
            style={{
              background: '#fff5f5',
              border: '1px solid #f5c2c7',
              borderRadius: 12,
              padding: 24,
              marginTop: 24,
            }}
          >
            <h2 style={{ color: '#dc3545', marginTop: 0 }}>Analysis could not be completed</h2>
            <p style={{ color: '#333' }}>{state.error}</p>
            <button
              onClick={reset}
              style={{
                padding: '8px 16px',
                background: '#4472C4',
                color: 'white',
                border: 'none',
                borderRadius: 6,
                cursor: 'pointer',
              }}
            >
              Start over
            </button>
          </div>
        )}

        {state.status === 'complete' && state.report && (
          <Dashboard
            report={state.report}
            trace={state.trace}
            sessionId={state.sessionId}
            onNewAnalysis={reset}
          />
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
