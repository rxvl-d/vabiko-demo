import React, { useState, useEffect } from 'react';
import axios from 'axios';

function PersonLinking() {
  const [linkingMethod, setLinkingMethod] = useState('v1');
  const [hasLinkFilter, setHasLinkFilter] = useState('');
  const [personTypeFilter, setPersonTypeFilter] = useState('');
  const [unifiedNames, setUnifiedNames] = useState([]);
  const [selectedUnifiedName, setSelectedUnifiedName] = useState('');
  const [personDetails, setPersonDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchUnifiedNames();
  }, [linkingMethod, hasLinkFilter, personTypeFilter]);

  const fetchUnifiedNames = async () => {
    try {
      const params = new URLSearchParams();
      params.append('method', linkingMethod);
      if (hasLinkFilter) {
        params.append('has_link', hasLinkFilter);
      }
      if (personTypeFilter) {
        params.append('person_type', personTypeFilter);
      }

      const response = await axios.get(`/api/linking/unified-names?${params}`);
      setUnifiedNames(response.data.unified_names);
      setSelectedUnifiedName('');
      setPersonDetails(null);
    } catch (error) {
      console.error('Error fetching unified names:', error);
      setError('Error loading unified names');
    }
  };

  const fetchPersonDetails = async () => {
    if (!selectedUnifiedName) return;

    setLoading(true);
    setError('');

    try {
      const params = new URLSearchParams();
      params.append('method', linkingMethod);
      if (personTypeFilter) {
        params.append('person_type', personTypeFilter);
      }
      
      const response = await axios.get(`/api/linking/unified-name/${encodeURIComponent(selectedUnifiedName)}?${params}`);
      setPersonDetails(response.data);
    } catch (error) {
      console.error('Error fetching person details:', error);
      setError('Error loading person details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedUnifiedName) {
      fetchPersonDetails();
    }
  }, [selectedUnifiedName, linkingMethod, personTypeFilter]);

  return (
    <div className="archive-browser">
      <h2>Person Linking Interface</h2>
      <p>Browse unified person names with Wikidata links and view their name mappings and associated images.</p>

      <div className="controls-section">
        <div style={{ display: 'flex', gap: '20px', marginBottom: '15px', flexWrap: 'wrap' }}>
          <div>
            <label><strong>Linking Method:</strong></label>
            <select
              value={linkingMethod}
              onChange={(e) => setLinkingMethod(e.target.value)}
              style={{ marginLeft: '10px', padding: '5px' }}
            >
              <option value="v1">V1 (linked_name)</option>
              <option value="v2">V2 (linked_name_v2)</option>
              <option value="v3">V3 (linked_name_v3)</option>
              <option value="v4">V4 (linked_name_v4)</option>
            </select>
          </div>

          <div>
            <label><strong>Person Type:</strong></label>
            <select
              value={personTypeFilter}
              onChange={(e) => setPersonTypeFilter(e.target.value)}
              style={{ marginLeft: '10px', padding: '5px' }}
            >
              <option value="">All Types</option>
              <option value="depicted_person">Depicted Person</option>
              <option value="photographer">Photographer</option>
            </select>
          </div>

          <div>
            <label><strong>Has Link Filter:</strong></label>
            <select
              value={hasLinkFilter}
              onChange={(e) => setHasLinkFilter(e.target.value)}
              style={{ marginLeft: '10px', padding: '5px' }}
            >
              <option value="">All</option>
              <option value="true">Has Link</option>
              <option value="false">No Link</option>
            </select>
          </div>
        </div>

        <div>
          <label><strong>Unified Name:</strong></label>
          <select
            value={selectedUnifiedName}
            onChange={(e) => setSelectedUnifiedName(e.target.value)}
            style={{ width: '100%', padding: '10px', fontSize: '16px', marginTop: '5px' }}
          >
            <option value="">
              Select a unified name... ({unifiedNames.length} available)
            </option>
            {unifiedNames.map((item) => (
              <option key={item.unified_name} value={item.unified_name}>
                {item.display_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {loading && <div className="loading">Loading person details...</div>}

      {personDetails && (
        <div>
          <h3>Details for "{personDetails.unified_name}"</h3>
          
          <div className="person-details">
            <div className="name-mappings">
              <h4>Name Mappings ({personDetails.total_existing_names})</h4>
              <div className="existing-names-list">
                {personDetails.existing_names.map((nameInfo, index) => (
                  <div key={index} className="name-mapping">
                    <div className="existing-name">
                      <strong>Original:</strong> {nameInfo.existing_name}
                      <div className="person-type-badge">
                        {nameInfo.person_type === 'depicted_person' ? 'Depicted Person' : 
                         nameInfo.person_type === 'photographer' ? 'Photographer' : 
                         nameInfo.person_type}
                      </div>
                    </div>
                    <div className="name-info">
                      <span className="image-count">{nameInfo.image_count} images</span>
                      {nameInfo.wikidata_link && (
                        <a 
                          href={nameInfo.wikidata_link} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="wikidata-link"
                        >
                          Wikidata Link
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {personDetails.wikidata_links.length > 0 && (
              <div className="wikidata-summary">
                <h4>Wikidata Links ({linkingMethod.toUpperCase()})</h4>
                {personDetails.wikidata_links.map((link, index) => (
                  <a 
                    key={index}
                    href={link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="wikidata-link"
                    style={{ display: 'block', marginBottom: '5px' }}
                  >
                    {link}
                  </a>
                ))}
              </div>
            )}
          </div>

          <div className="images-section">
            <h4>Associated Images ({personDetails.total_images})</h4>
            <div className="image-grid">
              {personDetails.images.map((image, index) => (
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
        </div>
      )}
    </div>
  );
}

export default PersonLinking;