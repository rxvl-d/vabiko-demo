import React, { useState } from 'react';
import axios from 'axios';

function ArchiveBrowser() {
  const [urn, setUrn] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const searchUrn = async () => {
    if (!urn.trim()) {
      setError('Please enter a URN');
      return;
    }

    setLoading(true);
    setError('');
    setData(null);

    try {
      const response = await axios.get(`/api/urn/${encodeURIComponent(urn.trim())}`);
      setData(response.data);
    } catch (error) {
      if (error.response?.status === 404) {
        setError(`URN not found: ${urn}`);
      } else {
        setError('Error fetching data. Please try again.');
      }
      console.error('Error fetching URN data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      searchUrn();
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-5">
      <h2 className="text-2xl font-bold mb-3">Archive Browser</h2>
      <p className="text-gray-600 mb-2">Enter a URN to view the corresponding image and metadata. URNs can use either : or + as separators.</p>
      <p className="text-gray-500 italic text-sm mb-5">Example: urn:nbn:de:hebis:30:2-586743 or urn+nbn+de+hebis+30+2-586743</p>

      <div className="flex mb-5">
        <input
          type="text"
          value={urn}
          onChange={(e) => setUrn(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Enter URN (e.g., urn:nbn:de:hebis:30:2-586743)"
          className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button 
          onClick={searchUrn} 
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white border border-blue-600 rounded-r-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && <div className="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}

      {data && (
        <div className="flex flex-col lg:flex-row gap-5 min-h-[400px]">
          <div className="flex-1 border border-gray-300 rounded p-4 bg-gray-50">
            <h3 className="text-lg font-semibold mb-3">Image</h3>
            {data.has_image ? (
              <img
                src={`/api/image/${encodeURIComponent(data.urn)}`}
                alt={`Image for ${data.urn}`}
                className="max-w-full h-auto rounded"
              />
            ) : (
              <p className="text-gray-500">No image available for this URN.</p>
            )}
          </div>

          <div className="flex-1 border border-gray-300 rounded p-4 bg-gray-50">
            <h3 className="text-lg font-semibold mb-3">Metadata (METS XML)</h3>
            {data.has_metadata ? (
              <pre className="whitespace-pre-wrap bg-white p-3 rounded border border-gray-200 text-xs leading-tight max-h-96 overflow-y-auto">
                {data.metadata}
              </pre>
            ) : (
              <p className="text-gray-500">No metadata available for this URN.</p>
            )}
            {data.metadata_error && (
              <div className="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded mt-3">
                Error loading metadata: {data.metadata_error}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default ArchiveBrowser;