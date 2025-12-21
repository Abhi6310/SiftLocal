'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import SeedInput from '@/components/SeedInput';
import { unlockVault } from '@/lib/api';

export default function UnlockPage() {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleUnlock = async (seedPhrase) => {
    setError('');
    setLoading(true);
    try {
      await unlockVault(seedPhrase);
      router.push('/');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-2xl w-full px-6">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Unlock SiftLocal
          </h1>
          <p className="text-gray-600 mb-8">
            Enter your 12-word BIP39 seed phrase to unlock your vault.
          </p>
          <SeedInput onSubmit={handleUnlock} error={error} />
          {loading && (
            <div className="mt-4 text-center text-gray-600">
              Unlocking vault...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
