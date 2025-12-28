const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function unlockVault(seedPhrase) {
  const response = await fetch(`${API_BASE}/api/auth/unlock`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ seed_phrase: seedPhrase })
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Unlock failed');
  }
  return response.json();
}

export async function lockVault() {
  const response = await fetch(`${API_BASE}/api/auth/lock`, {
    method: 'POST',
    credentials: 'include'
  });
  return response.json();
}

export async function getAuthStatus() {
  const response = await fetch(`${API_BASE}/api/auth/status`, {
    credentials: 'include'
  });
  return response.json();
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await fetch(`${API_BASE}/api/documents/upload`, {
    method: 'POST',
    credentials: 'include',
    body: formData
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }
  return response.json();
}

export async function getReviewQueue() {
  const response = await fetch(`${API_BASE}/api/review/queue`, {
    credentials: 'include'
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch review queue');
  }
  return response.json();
}
