import React from 'react';
import { Loader2 } from 'lucide-react';

interface BatchProgressProps {
  files: File[];
  progress: number;
}

export function BatchProgress({ files, progress }: BatchProgressProps) {
  const percentage = files.length > 0 ? Math.round((progress / files.length) * 100) : 0;

  return (
    <div
      style={{
        background: 'white',
        borderRadius: 12,
        padding: 32,
        marginTop: 24,
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <Loader2
          size={24}
          color="#4472C4"
          style={{ animation: 'spin 1s linear infinite' }}
        />
        <h2 style={{ color: '#1a1a2e', margin: 0 }}>Processing Documents</h2>
      </div>

      <div
        style={{
          background: '#e9ecef',
          borderRadius: 8,
          height: 12,
          overflow: 'hidden',
          marginBottom: 12,
        }}
      >
        <div
          style={{
            background: 'linear-gradient(90deg, #4472C4, #2196F3)',
            height: '100%',
            width: `${percentage}%`,
            transition: 'width 0.3s ease',
            borderRadius: 8,
          }}
        />
      </div>

      <p style={{ color: '#6c757d', margin: 0 }}>
        {progress} of {files.length} documents processed ({percentage}%)
      </p>

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
