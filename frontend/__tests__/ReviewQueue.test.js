import { render, screen } from '@testing-library/react';
import ReviewQueue from '@/components/ReviewQueue';

describe('ReviewQueue', () => {
  it('displays empty message when no chunks', () => {
    render(<ReviewQueue chunks={[]} totalCount={0} />);
    expect(screen.getByText(/no chunks pending review/i)).toBeInTheDocument();
  });

  it('displays chunk count', () => {
    const chunks = [
      {
        chunk_id: 'doc-1',
        document_id: 'doc-1',
        redacted_text: 'Test content',
        redactions: [],
        status: 'pending'
      }
    ];
    render(<ReviewQueue chunks={chunks} totalCount={1} />);
    expect(screen.getByText(/1 chunk in queue/i)).toBeInTheDocument();
  });

  it('renders redacted text with placeholders', () => {
    const chunks = [
      {
        chunk_id: 'doc-2',
        document_id: 'doc-2',
        redacted_text: 'Contact [EMAIL_ADDRESS_1] for help',
        redactions: [
          { placeholder: '[EMAIL_ADDRESS_1]', entity_type: 'EMAIL_ADDRESS', source: 'pii' }
        ],
        status: 'pending'
      }
    ];
    render(<ReviewQueue chunks={chunks} totalCount={1} />);
    expect(screen.getByText('[EMAIL_ADDRESS_1]')).toBeInTheDocument();
    expect(screen.getByText(/1 redaction$/)).toBeInTheDocument();
  });

  it('displays chunk status', () => {
    const chunks = [
      {
        chunk_id: 'doc-3',
        document_id: 'doc-3',
        redacted_text: 'Some text',
        redactions: [],
        status: 'pending'
      }
    ];
    render(<ReviewQueue chunks={chunks} totalCount={1} />);
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('highlights PII redactions with amber color', () => {
    const chunks = [
      {
        chunk_id: 'doc-4',
        document_id: 'doc-4',
        redacted_text: 'SSN: [US_SSN_1]',
        redactions: [
          { placeholder: '[US_SSN_1]', entity_type: 'US_SSN', source: 'pii' }
        ],
        status: 'pending'
      }
    ];
    render(<ReviewQueue chunks={chunks} totalCount={1} />);
    const redactionSpan = screen.getByText('[US_SSN_1]');
    expect(redactionSpan).toHaveStyle({ backgroundColor: '#fef3c7' });
  });

  it('highlights secret redactions with red color', () => {
    const chunks = [
      {
        chunk_id: 'doc-5',
        document_id: 'doc-5',
        redacted_text: 'Key: [AWS_ACCESS_KEY_1]',
        redactions: [
          { placeholder: '[AWS_ACCESS_KEY_1]', entity_type: 'AWS_ACCESS_KEY', source: 'secret' }
        ],
        status: 'pending'
      }
    ];
    render(<ReviewQueue chunks={chunks} totalCount={1} />);
    const redactionSpan = screen.getByText('[AWS_ACCESS_KEY_1]');
    expect(redactionSpan).toHaveStyle({ backgroundColor: '#fee2e2' });
  });

  it('renders multiple chunks', () => {
    const chunks = [
      { chunk_id: 'doc-a', document_id: 'doc-a', redacted_text: 'First', redactions: [], status: 'pending' },
      { chunk_id: 'doc-b', document_id: 'doc-b', redacted_text: 'Second', redactions: [], status: 'pending' }
    ];
    render(<ReviewQueue chunks={chunks} totalCount={2} />);
    expect(screen.getByText(/2 chunks in queue/i)).toBeInTheDocument();
    expect(screen.getByText('First')).toBeInTheDocument();
    expect(screen.getByText('Second')).toBeInTheDocument();
  });

  it('shows title on hover for redaction type', () => {
    const chunks = [
      {
        chunk_id: 'doc-6',
        document_id: 'doc-6',
        redacted_text: 'Email: [EMAIL_ADDRESS_1]',
        redactions: [
          { placeholder: '[EMAIL_ADDRESS_1]', entity_type: 'EMAIL_ADDRESS', source: 'pii' }
        ],
        status: 'pending'
      }
    ];
    render(<ReviewQueue chunks={chunks} totalCount={1} />);
    const redactionSpan = screen.getByText('[EMAIL_ADDRESS_1]');
    expect(redactionSpan).toHaveAttribute('title', 'EMAIL_ADDRESS (pii)');
  });
});
