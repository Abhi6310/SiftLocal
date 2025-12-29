'use client';

const buttonBase = {
  padding: '6px 12px',
  borderRadius: '4px',
  border: 'none',
  cursor: 'pointer',
  fontSize: '0.875rem',
  fontWeight: '500',
  transition: 'background-color 0.15s'
};

const approveStyle = {
  ...buttonBase,
  backgroundColor: '#059669',
  color: 'white'
};

const rejectStyle = {
  ...buttonBase,
  backgroundColor: '#dc2626',
  color: 'white'
};

const disabledStyle = {
  opacity: 0.5,
  cursor: 'not-allowed'
};

export function ChunkActions({ chunkId, status, onApprove, onReject, disabled }) {
  const isApproved = status === 'approved';
  const isRejected = status === 'rejected';
  return (
    <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
      <button
        onClick={() => onApprove(chunkId)}
        disabled={disabled || isApproved}
        style={{
          ...approveStyle,
          ...(disabled || isApproved ? disabledStyle : {})
        }}
      >
        {isApproved ? 'Approved' : 'Approve'}
      </button>
      <button
        onClick={() => onReject(chunkId)}
        disabled={disabled || isRejected}
        style={{
          ...rejectStyle,
          ...(disabled || isRejected ? disabledStyle : {})
        }}
      >
        {isRejected ? 'Rejected' : 'Reject'}
      </button>
    </div>
  );
}

export function BulkActions({ selectedIds, onBulkApprove, onBulkReject, disabled }) {
  const count = selectedIds.length;
  if (count === 0) return null;
  return (
    <div style={{
      display: 'flex',
      gap: '12px',
      alignItems: 'center',
      padding: '12px 16px',
      backgroundColor: '#f3f4f6',
      borderRadius: '8px',
      marginBottom: '16px'
    }}>
      <span style={{ fontWeight: '500' }}>
        {count} selected
      </span>
      <button
        onClick={() => onBulkApprove(selectedIds)}
        disabled={disabled}
        style={{
          ...approveStyle,
          ...(disabled ? disabledStyle : {})
        }}
      >
        Approve All
      </button>
      <button
        onClick={() => onBulkReject(selectedIds)}
        disabled={disabled}
        style={{
          ...rejectStyle,
          ...(disabled ? disabledStyle : {})
        }}
      >
        Reject All
      </button>
    </div>
  );
}

export function SelectCheckbox({ checked, onChange, disabled }) {
  return (
    <input
      type="checkbox"
      checked={checked}
      onChange={(e) => onChange(e.target.checked)}
      disabled={disabled}
      style={{ cursor: disabled ? 'not-allowed' : 'pointer', width: '16px', height: '16px' }}
    />
  );
}

export function SelectAllCheckbox({ allSelected, someSelected, onToggle, disabled }) {
  return (
    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: disabled ? 'not-allowed' : 'pointer' }}>
      <input
        type="checkbox"
        checked={allSelected}
        ref={(el) => {
          if (el) el.indeterminate = someSelected && !allSelected;
        }}
        onChange={(e) => onToggle(e.target.checked)}
        disabled={disabled}
        style={{ width: '16px', height: '16px' }}
      />
      <span style={{ fontSize: '0.875rem', color: '#666' }}>Select all</span>
    </label>
  );
}
