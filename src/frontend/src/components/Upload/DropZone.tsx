import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText } from 'lucide-react';

interface DropZoneProps {
  onFilesSelected: (files: File[]) => void;
}

export function DropZone({ onFilesSelected }: DropZoneProps) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length > 0) onFilesSelected(accepted);
    },
    [onFilesSelected]
  );

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxSize: 50 * 1024 * 1024,
    maxFiles: 100,
  });

  return (
    <div style={{ marginTop: 24 }}>
      <div
        {...getRootProps()}
        style={{
          border: `3px dashed ${isDragActive ? '#4472C4' : '#dee2e6'}`,
          borderRadius: 12,
          padding: 60,
          textAlign: 'center',
          cursor: 'pointer',
          background: isDragActive ? '#e8f0fe' : 'white',
          transition: 'all 0.2s',
        }}
      >
        <input {...getInputProps()} />
        <Upload size={48} color="#4472C4" style={{ marginBottom: 16 }} />
        <h2 style={{ color: '#1a1a2e', marginBottom: 8 }}>
          {isDragActive ? 'Drop documents here' : 'Upload Legal Documents'}
        </h2>
        <p style={{ color: '#6c757d' }}>
          Drag & drop PDF, DOCX, or TXT files here, or click to browse
        </p>
        <p style={{ color: '#adb5bd', fontSize: '0.85em', marginTop: 8 }}>
          Max 100 files, 50MB each
        </p>
      </div>

      {acceptedFiles.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <h3 style={{ color: '#1a1a2e', marginBottom: 8 }}>
            Selected Files ({acceptedFiles.length})
          </h3>
          {acceptedFiles.map((file, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '8px 12px',
                background: '#f8f9fa',
                borderRadius: 6,
                marginBottom: 4,
              }}
            >
              <FileText size={16} color="#4472C4" />
              <span style={{ flex: 1 }}>{file.name}</span>
              <span style={{ color: '#6c757d', fontSize: '0.85em' }}>
                {(file.size / 1024).toFixed(0)} KB
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
