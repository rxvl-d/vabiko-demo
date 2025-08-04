import React, { useState, useEffect } from 'react';
import axios from 'axios';

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

export default PeopleBrowser;