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

export async function approveChunk(chunkId) {
  const response = await fetch(`${API_BASE}/api/review/${chunkId}/approve`, {
    method: 'POST',
    credentials: 'include'
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to approve chunk');
  }
  return response.json();
}

export async function rejectChunk(chunkId) {
  const response = await fetch(`${API_BASE}/api/review/${chunkId}/reject`, {
    method: 'POST',
    credentials: 'include'
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to reject chunk');
  }
  return response.json();
}

export async function bulkApprove(chunkIds) {
  const response = await fetch(`${API_BASE}/api/review/bulk/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ chunk_ids: chunkIds })
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to bulk approve');
  }
  return response.json();
}

export async function bulkReject(chunkIds) {
  const response = await fetch(`${API_BASE}/api/review/bulk/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ chunk_ids: chunkIds })
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to bulk reject');
  }
  return response.json();
}

export async function getReviewCounts() {
  const response = await fetch(`${API_BASE}/api/review/counts`, {
    credentials: 'include'
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch review counts');
  }
  return response.json();
}
