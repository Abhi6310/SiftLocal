'use client';
import { useState } from 'react';

export default function SeedInput({ onSubmit, error }) {
  const [words, setWords] = useState(Array(12).fill(''));

  const handleWordChange = (index, value) => {
    const newWords = [...words];
    newWords[index] = value.toLowerCase().trim();
    setWords(newWords);
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (index < 11) {
        document.getElementById(`word-${index + 1}`).focus();
      } else {
        handleSubmit();
      }
    }
  };

  const handleSubmit = () => {
    const seedPhrase = words.join(' ');
    onSubmit(seedPhrase);
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        {words.map((word, index) => (
          <div key={index} className="flex items-center space-x-2">
            <span className="text-sm text-gray-500 w-6">{index + 1}.</span>
            <input
              id={`word-${index}`}
              type="text"
              value={word}
              onChange={(e) => handleWordChange(index, e.target.value)}
              onKeyDown={(e) => handleKeyDown(index, e)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus={index === 0}
              autoComplete="off"
              spellCheck="false"
            />
          </div>
        ))}
      </div>
      {error && <div className="text-red-600 text-sm">{error}</div>}
      <button
        onClick={handleSubmit}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        Unlock Vault
      </button>
    </div>
  );
}
