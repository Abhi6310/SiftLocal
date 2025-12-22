'use client';
import { useState } from 'react';
import FileUpload from '@/components/FileUpload';
import { uploadDocument } from '@/lib/api';

export default function UploadPage() {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleUpload = async (file, validationError) => {
    if (validationError) { setError(validationError); return; }
    setError('');
    setLoading(true);
    setResult(null);
    try {
      setResult(await uploadDocument(file));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main>
      <h1>Upload Document</h1>
      <FileUpload onUpload={handleUpload} error={error} />
      {loading && <p>Uploading...</p>}
      {result && (
        <div>
          <p>ID: {result.document_id}</p>
          <p>File: {result.filename}</p>
          <p>Type: {result.file_type}</p>
          <p>Size: {result.size} bytes</p>
          <p>SHA-256: {result.sha256}</p>
        </div>
      )}
    </main>
  );
}
