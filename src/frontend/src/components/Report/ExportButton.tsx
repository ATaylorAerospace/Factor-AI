import React, { useState } from 'react';
import { Download } from 'lucide-react';
import { exportReport } from '../../api/client';

interface ExportButtonProps {
  sessionId: string;
}

export function ExportButton({ sessionId }: ExportButtonProps) {
  const [exporting, setExporting] = useState(false);

  const handleExport = async (format: 'excel' | 'html') => {
    setExporting(true);
    try {
      const result = await exportReport(sessionId, format);
      alert(`Report exported to: ${result.path}`);
    } catch (err) {
      alert(`Export failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div style={{ display: 'flex', gap: 8 }}>
      <button
        onClick={() => handleExport('excel')}
        disabled={exporting}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          padding: '8px 16px',
          background: '#28a745',
          color: 'white',
          border: 'none',
          borderRadius: 6,
          cursor: exporting ? 'not-allowed' : 'pointer',
          opacity: exporting ? 0.6 : 1,
          fontSize: '0.9em',
        }}
      >
        <Download size={16} />
        Excel
      </button>
      <button
        onClick={() => handleExport('html')}
        disabled={exporting}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          padding: '8px 16px',
          background: '#4472C4',
          color: 'white',
          border: 'none',
          borderRadius: 6,
          cursor: exporting ? 'not-allowed' : 'pointer',
          opacity: exporting ? 0.6 : 1,
          fontSize: '0.9em',
        }}
      >
        <Download size={16} />
        HTML
      </button>
    </div>
  );
}
