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
    <div className="bg-white rounded-lg shadow-sm p-5">
      <h2 className="text-2xl font-bold mb-3">Person Linking Interface</h2>
      <p className="text-gray-600 mb-5">Browse unified person names with Wikidata links and view their name mappings and associated images.</p>

      <div className="bg-gray-50 p-5 rounded-lg border border-gray-200 mb-5">
        <div className="flex flex-wrap gap-5 mb-4">
          <div className="flex flex-col">
            <label className="font-semibold mb-1">Linking Method:</label>
            <select
              value={linkingMethod}
              onChange={(e) => setLinkingMethod(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="v1">V1 (linked_name)</option>
              <option value="v2">V2 (linked_name_v2)</option>
              <option value="v3">V3 (linked_name_v3)</option>
              <option value="v4">V4 (linked_name_v4)</option>
            </select>
          </div>

          <div className="flex flex-col">
            <label className="font-semibold mb-1">Person Type:</label>
            <select
              value={personTypeFilter}
              onChange={(e) => setPersonTypeFilter(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Types</option>
              <option value="depicted_person">Depicted Person</option>
              <option value="photographer">Photographer</option>
            </select>
          </div>

          <div className="flex flex-col">
            <label className="font-semibold mb-1">Has Link Filter:</label>
            <select
              value={hasLinkFilter}
              onChange={(e) => setHasLinkFilter(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All</option>
              <option value="true">Has Link</option>
              <option value="false">No Link</option>
            </select>
          </div>
        </div>

        <div className="flex flex-col">
          <label className="font-semibold mb-2">Unified Name:</label>
          <select
            value={selectedUnifiedName}
            onChange={(e) => setSelectedUnifiedName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
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

      {error && <div className="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}

      {loading && <div className="text-center py-5 text-gray-600">Loading person details...</div>}

      {personDetails && (
        <div>
          <h3 className="text-xl font-bold mb-5">Details for "{personDetails.unified_name}"</h3>
          
          <div className="flex flex-col lg:flex-row gap-8 mb-8">
            <div className="flex-1">
              <h4 className="text-lg font-semibold mb-3">Name Mappings ({personDetails.total_existing_names})</h4>
              <div className="max-h-80 overflow-y-auto border border-gray-300 rounded p-3 bg-white">
                {personDetails.existing_names.map((nameInfo, index) => (
                  <div key={index} className="flex justify-between items-center py-3 border-b border-gray-200 last:border-b-0">
                    <div className="flex-1">
                      <div className="font-semibold">Original: {nameInfo.existing_name}</div>
                      {nameInfo.person_type && (
                        <div className="inline-block bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs font-semibold mt-1">
                          {nameInfo.person_type === 'depicted_person' ? 'Depicted Person' : 
                           nameInfo.person_type === 'photographer' ? 'Photographer' : 
                           nameInfo.person_type}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-semibold">
                        {nameInfo.image_count} images
                      </span>
                      {nameInfo.wikidata_link && (
                        <a 
                          href={nameInfo.wikidata_link} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="bg-green-600 text-white px-2 py-1 rounded text-xs font-semibold hover:bg-green-700"
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
              <div className="flex-1">
                <h4 className="text-lg font-semibold mb-3">Wikidata Links ({linkingMethod.toUpperCase()})</h4>
                <div className="space-y-2">
                  {personDetails.wikidata_links.map((link, index) => (
                    <a 
                      key={index}
                      href={link} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="block bg-green-600 text-white px-3 py-2 rounded hover:bg-green-700 text-sm font-semibold"
                    >
                      {link}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="mt-8">
            <h4 className="text-lg font-semibold mb-5">Associated Images ({personDetails.total_images})</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {personDetails.images.map((image, index) => (
                <div key={image.urn || index} className="border border-gray-300 rounded-lg overflow-hidden bg-white shadow-sm">
                  {image.has_image && (
                    <img
                      src={`/api/image/${encodeURIComponent(image.urn)}`}
                      alt={image.title || 'Archive image'}
                      className="w-full h-48 object-cover"
                    />
                  )}
                  <div className="p-4">
                    <p className="text-sm mb-1"><span className="font-semibold">URN:</span> {image.urn}</p>
                    {image.title && <p className="text-sm mb-1"><span className="font-semibold">Title:</span> {image.title}</p>}
                    {image.content_keywords.length > 0 && (
                      <p className="text-sm mb-1"><span className="font-semibold">Keywords:</span> {image.content_keywords.join(', ')}</p>
                    )}
                    {image.subject_location.length > 0 && (
                      <p className="text-sm"><span className="font-semibold">Location:</span> {image.subject_location.join(', ')}</p>
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