import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [interfaces, setInterfaces] = useState([]);
  const [selectedInterface, setSelectedInterface] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInterfaces();
  }, []);

  const fetchInterfaces = async () => {
    try {
      const response = await axios.get('/api/interfaces');
      setInterfaces(response.data);
      if (response.data.length > 0) {
        setSelectedInterface(response.data[0].id);
      }
    } catch (error) {
      console.error('Error fetching interfaces:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="container">
      <div className="header">
        <h1>VABiKo Demo Application</h1>
        <p>Explore various features and interfaces for the VABiKo image archive</p>
      </div>

      <div className="interface-selector">
        <label htmlFor="interface-select">
          <strong>Select Interface:</strong>
        </label>
        <select
          id="interface-select"
          value={selectedInterface}
          onChange={(e) => setSelectedInterface(e.target.value)}
        >
          <option value="">Choose an interface...</option>
          {interfaces.map((iface) => (
            <option key={iface.id} value={iface.id}>
              {iface.name} - {iface.description}
            </option>
          ))}
        </select>
      </div>

      {selectedInterface === 'archive_browser' && <ArchiveBrowser />}
      {selectedInterface === 'people_browser' && <PeopleBrowser />}
    </div>
  );
}

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

function PeopleBrowser() {
  const [searchType, setSearchType] = useState('depicted');
  const [people, setPeople] = useState([]);
  const [selectedPerson, setSelectedPerson] = useState('');
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPeople();
  }, [searchType]);

  const fetchPeople = async () => {
    try {
      const endpoint = searchType === 'depicted' ? '/api/people/depicted' : '/api/people/photographers';
      const response = await axios.get(endpoint);
      const peopleList = searchType === 'depicted' ? response.data.persons : response.data.photographers;
      setPeople(peopleList);
      setSelectedPerson('');
      setImages([]);
    } catch (error) {
      console.error('Error fetching people:', error);
      setError('Error loading people list');
    }
  };

  const fetchImagesByPerson = async () => {
    if (!selectedPerson) return;

    setLoading(true);
    setError('');

    try {
      const endpoint = searchType === 'depicted' 
        ? `/api/people/depicted/${encodeURIComponent(selectedPerson)}`
        : `/api/people/photographers/${encodeURIComponent(selectedPerson)}`;
      
      const response = await axios.get(endpoint);
      setImages(response.data.images);
    } catch (error) {
      console.error('Error fetching images:', error);
      setError('Error loading images');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedPerson) {
      fetchImagesByPerson();
    }
  }, [selectedPerson]);

  return (
    <div className="archive-browser">
      <h2>People Browser</h2>
      <p>Browse images by depicted persons or photographers from the VABiKo archive.</p>

      <div className="search-section">
        <div style={{ marginBottom: '10px' }}>
          <label>
            <input
              type="radio"
              value="depicted"
              checked={searchType === 'depicted'}
              onChange={(e) => setSearchType(e.target.value)}
            />
            Depicted Persons
          </label>
          <label style={{ marginLeft: '20px' }}>
            <input
              type="radio"
              value="photographers"
              checked={searchType === 'photographers'}
              onChange={(e) => setSearchType(e.target.value)}
            />
            Photographers
          </label>
        </div>

        <select
          value={selectedPerson}
          onChange={(e) => setSelectedPerson(e.target.value)}
          style={{ width: '100%', padding: '10px', fontSize: '16px' }}
        >
          <option value="">
            Select a {searchType === 'depicted' ? 'person' : 'photographer'}... ({people.length} available)
          </option>
          {people.map((person) => (
            <option key={person.name || person} value={person.name || person}>
              {person.display_name || person}
            </option>
          ))}
        </select>
      </div>

      {error && <div className="error">{error}</div>}

      {loading && <div className="loading">Loading images...</div>}

      {images.length > 0 && (
        <div>
          <h3>
            Images {searchType === 'depicted' ? 'depicting' : 'by'} "{selectedPerson}" ({images.length} found)
          </h3>
          <div className="image-grid">
            {images.map((image, index) => (
              <div key={image.urn || index} className="image-card">
                {image.has_image && (
                  <img
                    src={`/api/image/${encodeURIComponent(image.urn)}`}
                    alt={image.title || 'Archive image'}
                    className="grid-image"
                  />
                )}
                <div className="image-info">
                  <p><strong>URN:</strong> {image.urn}</p>
                  {image.title && <p><strong>Title:</strong> {image.title}</p>}
                  {image.content_keywords.length > 0 && (
                    <p><strong>Keywords:</strong> {image.content_keywords.join(', ')}</p>
                  )}
                  {image.subject_location.length > 0 && (
                    <p><strong>Location:</strong> {image.subject_location.join(', ')}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;