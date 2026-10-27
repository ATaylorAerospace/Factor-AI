import { useCallback, useState } from 'react';
import { useDropzone, type FileRejection } from 'react-dropzone';
import { Upload, FileText, AlertTriangle } from 'lucide-react';

interface DropZoneProps {
  onFilesSelected: (files: File[]) => void;
}

const MAX_FILE_BYTES = 50 * 1024 * 1024;
const MAX_FILES = 100;

/** Human-readable reason for a file react-dropzone refused. */
function rejectionReason(rejection: FileRejection): string {
  const code = rejection.errors[0]?.code;
  switch (code) {
    case 'file-too-large':
      return 'exceeds the 50 MB limit';
    case 'file-invalid-type':
      return 'is not a PDF, DOCX, or TXT file';
    case 'too-many-files':
      return `is over the ${MAX_FILES}-file batch limit`;
    default:
      return rejection.errors[0]?.message ?? 'could not be added';
  }
}

export function DropZone({ onFilesSelected }: DropZoneProps) {
  const [rejected, setRejected] = useState<string[]>([]);

  const onDrop = useCallback(
    (accepted: File[], rejections: FileRejection[]) => {
      // Files that fail validation were previously dropped silently, so a user
      // who selected only a 60 MB PDF saw nothing happen at all.
      setRejected(rejections.map((r) => `${r.file.name} ${rejectionReason(r)}`));
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
    maxSize: MAX_FILE_BYTES,
    maxFiles: MAX_FILES,
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
          Max {MAX_FILES} files, 50MB each
        </p>
      </div>

      {rejected.length > 0 && (
        <div
          role="alert"
          style={{
            marginTop: 16,
            padding: '12px 16px',
            background: '#fff5f5',
            border: '1px solid #f5c2c7',
            borderRadius: 8,
            color: '#842029',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <AlertTriangle size={16} />
            <strong>Not added ({rejected.length})</strong>
          </div>
          {rejected.map((msg, i) => (
            <div key={i} style={{ fontSize: '0.9em' }}>{msg}</div>
          ))}
        </div>
      )}

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
