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
    <div className="bg-white rounded-lg shadow-sm p-5">
      <h2 className="text-2xl font-bold mb-3">People Browser</h2>
      <p className="text-gray-600 mb-5">Browse images by depicted persons or photographers from the VABiKo archive.</p>

      <div className="mb-5">
        <div className="flex gap-5 mb-3">
          <label className="flex items-center">
            <input
              type="radio"
              value="depicted"
              checked={searchType === 'depicted'}
              onChange={(e) => setSearchType(e.target.value)}
              className="mr-2"
            />
            Depicted Persons
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              value="photographers"
              checked={searchType === 'photographers'}
              onChange={(e) => setSearchType(e.target.value)}
              className="mr-2"
            />
            Photographers
          </label>
        </div>

        <select
          value={selectedPerson}
          onChange={(e) => setSelectedPerson(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
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

      {error && <div className="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}

      {loading && <div className="text-center py-5 text-gray-600">Loading images...</div>}

      {images.length > 0 && (
        <div>
          <h3 className="text-xl font-semibold mb-5">
            Images {searchType === 'depicted' ? 'depicting' : 'by'} "{selectedPerson}" ({images.length} found)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {images.map((image, index) => (
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
      )}
    </div>
  );
}

export default PeopleBrowser;