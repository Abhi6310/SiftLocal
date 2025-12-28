'use client';
import RedactionHighlight from './RedactionHighlight';

const STATUS_STYLES = {
  pending: { color: '#d97706', label: 'Pending' },
  approved: { color: '#059669', label: 'Approved' },
  rejected: { color: '#dc2626', label: 'Rejected' }
};

export default function ReviewQueue({ chunks, totalCount }) {
  if (!chunks || chunks.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        No chunks pending review
      </div>
    );
  }
  return (
    <div>
      <div style={{ marginBottom: '16px', color: '#666' }}>
        {totalCount} chunk{totalCount !== 1 ? 's' : ''} in queue
      </div>
      {chunks.map((chunk) => {
        const statusStyle = STATUS_STYLES[chunk.status] || STATUS_STYLES.pending;
        return (
          <div
            key={chunk.chunk_id}
            style={{
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '12px',
              backgroundColor: '#fff'
            }}
          >
            <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontFamily: 'monospace', fontSize: '0.85em', color: '#666' }}>
                {chunk.chunk_id}
              </span>
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
          </div>
        );
      })}
    </div>
  );
}
