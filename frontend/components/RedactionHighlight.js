'use client';

const COLORS = {
  pii: { bg: '#fef3c7', border: '#f59e0b' },
  secret: { bg: '#fee2e2', border: '#ef4444' }
};

export default function RedactionHighlight({ text, redactions }) {
  if (!redactions || redactions.length === 0) {
    return <span>{text}</span>;
  }
  //build a map of placeholder -> redaction info
  const redactionMap = {};
  for (const r of redactions) {
    redactionMap[r.placeholder] = r;
  }
  //split text by placeholders and render with highlights
  const placeholderPattern = /(\[[A-Z_]+_\d+\])/g;
  const parts = text.split(placeholderPattern);
  return (
    <span>
      {parts.map((part, i) => {
        const redaction = redactionMap[part];
        if (redaction) {
          const colors = COLORS[redaction.source] || COLORS.pii;
          return (
            <span
              key={i}
              style={{
                backgroundColor: colors.bg,
                border: `1px solid ${colors.border}`,
                borderRadius: '3px',
                padding: '1px 4px',
                margin: '0 1px',
                fontSize: '0.9em',
                fontFamily: 'monospace'
              }}
              title={`${redaction.entity_type} (${redaction.source})`}
            >
              {part}
            </span>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </span>
  );
}
