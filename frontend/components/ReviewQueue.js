'use client';
import { useState } from 'react';
import RedactionHighlight from './RedactionHighlight';
import { ChunkActions, BulkActions, SelectCheckbox, SelectAllCheckbox } from './ReviewActions';
import { approveChunk, rejectChunk, bulkApprove, bulkReject } from '@/lib/api';

const STATUS_STYLES = {
  pending: { color: '#d97706', label: 'Pending' },
  approved: { color: '#059669', label: 'Approved' },
  rejected: { color: '#dc2626', label: 'Rejected' }
};

export default function ReviewQueue({ chunks, totalCount, onRefresh }) {
  const [selected, setSelected] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!chunks || chunks.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        No chunks pending review
      </div>
    );
  }

  const pendingChunks = chunks.filter(c => c.status === 'pending');
  const allPendingSelected = pendingChunks.length > 0 && pendingChunks.every(c => selected.has(c.chunk_id));
  const somePendingSelected = pendingChunks.some(c => selected.has(c.chunk_id));

  const handleSelectOne = (chunkId, isSelected) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (isSelected) next.add(chunkId);
      else next.delete(chunkId);
      return next;
    });
  };

  const handleSelectAll = (selectAll) => {
    if (selectAll) {
      setSelected(new Set(pendingChunks.map(c => c.chunk_id)));
    } else {
      setSelected(new Set());
    }
  };

  const handleApprove = async (chunkId) => {
    setLoading(true);
    setError('');
    try {
      await approveChunk(chunkId);
      setSelected(prev => {
        const next = new Set(prev);
        next.delete(chunkId);
        return next;
      });
      if (onRefresh) onRefresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (chunkId) => {
    setLoading(true);
    setError('');
    try {
      await rejectChunk(chunkId);
      setSelected(prev => {
        const next = new Set(prev);
        next.delete(chunkId);
        return next;
      });
      if (onRefresh) onRefresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkApprove = async (chunkIds) => {
    setLoading(true);
    setError('');
    try {
      await bulkApprove(chunkIds);
      setSelected(new Set());
      if (onRefresh) onRefresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkReject = async (chunkIds) => {
    setLoading(true);
    setError('');
    try {
      await bulkReject(chunkIds);
      setSelected(new Set());
      if (onRefresh) onRefresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ color: '#666' }}>
          {totalCount} chunk{totalCount !== 1 ? 's' : ''} in queue
        </span>
        {pendingChunks.length > 0 && (
          <SelectAllCheckbox
            allSelected={allPendingSelected}
            someSelected={somePendingSelected}
            onToggle={handleSelectAll}
            disabled={loading}
          />
        )}
      </div>
      {error && <div style={{ color: '#dc2626', marginBottom: '12px' }}>{error}</div>}
      <BulkActions
        selectedIds={Array.from(selected)}
        onBulkApprove={handleBulkApprove}
        onBulkReject={handleBulkReject}
        disabled={loading}
      />
      {chunks.map((chunk) => {
        const statusStyle = STATUS_STYLES[chunk.status] || STATUS_STYLES.pending;
        const isPending = chunk.status === 'pending';
        return (
          <div
            key={chunk.chunk_id}
            style={{
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '12px',
              backgroundColor: selected.has(chunk.chunk_id) ? '#f0f9ff' : '#fff'
            }}
          >
            <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                {isPending && (
                  <SelectCheckbox
                    checked={selected.has(chunk.chunk_id)}
                    onChange={(isSelected) => handleSelectOne(chunk.chunk_id, isSelected)}
                    disabled={loading}
                  />
                )}
                <span style={{ fontFamily: 'monospace', fontSize: '0.85em', color: '#666' }}>
                  {chunk.chunk_id}
                </span>
              </div>
              <span style={{ color: statusStyle.color, fontWeight: '500', fontSize: '0.9em' }}>
                {statusStyle.label}
              </span>
            </div>
            <div style={{ lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
              <RedactionHighlight text={chunk.redacted_text} redactions={chunk.redactions} />
            </div>
            {chunk.redactions && chunk.redactions.length > 0 && (
              <div style={{ marginTop: '12px', fontSize: '0.85em', color: '#666' }}>
                {chunk.redactions.length} redaction{chunk.redactions.length !== 1 ? 's' : ''}
              </div>
            )}
            <ChunkActions
              chunkId={chunk.chunk_id}
              status={chunk.status}
              onApprove={handleApprove}
              onReject={handleReject}
              disabled={loading}
            />
          </div>
        );
      })}
    </div>
  );
}
