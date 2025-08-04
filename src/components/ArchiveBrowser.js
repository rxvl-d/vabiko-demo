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
    <div className="archive-browser">
      <h2>Archive Browser</h2>
      <p>Enter a URN to view the corresponding image and metadata. URNs can use either : or + as separators.</p>
      <p><em>Example: urn:nbn:de:hebis:30:2-586743 or urn+nbn+de+hebis+30+2-586743</em></p>

      <div className="search-section">
        <input
          type="text"
          value={urn}
          onChange={(e) => setUrn(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Enter URN (e.g., urn:nbn:de:hebis:30:2-586743)"
        />
        <button onClick={searchUrn} disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {data && (
        <div className="content-area">
          <div className="image-panel">
            <h3>Image</h3>
            {data.has_image ? (
              <img
                src={`/api/image/${encodeURIComponent(data.urn)}`}
                alt={`Image for ${data.urn}`}
              />
            ) : (
              <p>No image available for this URN.</p>
            )}
          </div>

          <div className="metadata-panel">
            <h3>Metadata (METS XML)</h3>
            {data.has_metadata ? (
              <pre>{data.metadata}</pre>
            ) : (
              <p>No metadata available for this URN.</p>
            )}
            {data.metadata_error && (
              <div className="error">
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