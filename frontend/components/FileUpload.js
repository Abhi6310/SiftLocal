'use client';
import { useState, useRef } from 'react';

const ALLOWED = ['.pdf', '.pptx', '.csv', '.txt'];

export default function FileUpload({ onUpload, error }) {
  const [file, setFile] = useState(null);
  const inputRef = useRef(null);

  const handleChange = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const ext = '.' + f.name.split('.').pop().toLowerCase();
    if (!ALLOWED.includes(ext)) {
      onUpload(null, `Invalid type. Allowed: ${ALLOWED.join(', ')}`);
      return;
    }
    setFile(f);
  };

  const handleSubmit = () => {
    if (file) onUpload(file, null);
  };

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept={ALLOWED.join(',')}
        onChange={handleChange}
      />
      {file && <p>{file.name} ({(file.size / 1024).toFixed(1)} KB)</p>}
      {error && <p style={{color: 'red'}}>{error}</p>}
      <button onClick={handleSubmit} disabled={!file}>Upload</button>
    </div>
  );
}
