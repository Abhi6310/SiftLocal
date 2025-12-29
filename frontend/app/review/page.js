'use client';
import { useState, useEffect } from 'react';
import ReviewQueue from '@/components/ReviewQueue';
import { getReviewQueue } from '@/lib/api';

export default function ReviewPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchQueue();
  }, []);

  const fetchQueue = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await getReviewQueue();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '24px' }}>Review Queue</h1>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {data && <ReviewQueue chunks={data.chunks} totalCount={data.total_count} onRefresh={fetchQueue} />}
      <button
        onClick={fetchQueue}
        disabled={loading}
        style={{
          marginTop: '16px',
          padding: '8px 16px',
          cursor: loading ? 'not-allowed' : 'pointer'
        }}
      >
        Refresh
      </button>
    </main>
  );
}
