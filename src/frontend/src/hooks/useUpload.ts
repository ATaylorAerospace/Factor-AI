import { useState, useCallback } from 'react';

interface UploadState {
  files: File[];
  isDragging: boolean;
}

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const MAX_FILES = 100;
const ACCEPTED_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
];

export function useUpload() {
  const [state, setState] = useState<UploadState>({
    files: [],
    isDragging: false,
  });

  const validateFiles = useCallback((files: File[]): { valid: File[]; errors: string[] } => {
    const valid: File[] = [];
    const errors: string[] = [];

    if (files.length > MAX_FILES) {
      errors.push(`Maximum ${MAX_FILES} files allowed`);
      return { valid, errors };
    }

    for (const file of files) {
      if (file.size > MAX_FILE_SIZE) {
        errors.push(`${file.name}: exceeds 50MB limit`);
        continue;
      }
      valid.push(file);
    }

    return { valid, errors };
  }, []);

  const addFiles = useCallback((newFiles: File[]) => {
    const { valid } = validateFiles(newFiles);
    setState((prev) => ({
      ...prev,
      files: [...prev.files, ...valid].slice(0, MAX_FILES),
    }));
  }, [validateFiles]);

  const removeFile = useCallback((index: number) => {
    setState((prev) => ({
      ...prev,
      files: prev.files.filter((_, i) => i !== index),
    }));
  }, []);

  const clearFiles = useCallback(() => {
    setState({ files: [], isDragging: false });
  }, []);

  const setDragging = useCallback((isDragging: boolean) => {
    setState((prev) => ({ ...prev, isDragging }));
  }, []);

  return {
    files: state.files,
    isDragging: state.isDragging,
    addFiles,
    removeFile,
    clearFiles,
    setDragging,
    validateFiles,
  };
}
