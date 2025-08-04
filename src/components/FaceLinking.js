import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ImageDisplay from './ImageDisplay';

function FaceLinking() {
  const [linkedPersons, setLinkedPersons] = useState([]);
  const [selectedPerson, setSelectedPerson] = useState('');
  const [personData, setPersonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchLinkedPersons();
  }, []);

  const fetchLinkedPersons = async () => {
    try {
      const response = await axios.get('/api/faces/linked-persons');
      setLinkedPersons(response.data.persons);
      setSelectedPerson('');
      setPersonData(null);
    } catch (error) {
      console.error('Error fetching linked persons:', error);
      setError('Error loading linked persons');
    }
  };

  const fetchPersonData = async () => {
    if (!selectedPerson) return;

    setLoading(true);
    setError('');

    try {
      const response = await axios.get(`/api/faces/person/${encodeURIComponent(selectedPerson)}`);
      setPersonData(response.data);
    } catch (error) {
      console.error('Error fetching person data:', error);
      setError('Error loading person data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedPerson) {
      fetchPersonData();
    }
  }, [selectedPerson]);

  const FaceBox = ({ face, imageUrn }) => (
    <div className="absolute border-2 border-red-500 bg-red-500 bg-opacity-20">
      <div className="absolute -top-6 left-0 bg-red-500 text-white px-2 py-1 text-xs rounded">
        Face {face.id}
      </div>
    </div>
  );

  const ImageWithFaces = ({ image, personData }) => {
    const [imageLoaded, setImageLoaded] = useState(false);
    const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });

    const handleImageLoad = (e) => {
      setImageLoaded(true);
      setImageDimensions({
        width: e.target.naturalWidth,
        height: e.target.naturalHeight
      });
    };

    return (
      <div className="border border-gray-300 rounded-lg overflow-hidden bg-white shadow-sm">
        <div className="relative">
          <ImageDisplay
            src={`/api/image-with-faces/${encodeURIComponent(image.urn)}`}
            alt={image.title || 'Archive image'}
            className="w-full"
            containerHeight="h-64"
          />
          {image.face_count > 0 && (
            <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded text-sm font-semibold">
              {(() => {
                // Find best similarity for this image
                const bestMatch = personData.face_similarity?.similarities?.filter(s => s.archive_urn === image.urn)
                  .sort((a, b) => b.similarity - a.similarity)[0];
                
                if (bestMatch) {
                  return `${(bestMatch.similarity * 100).toFixed(0)}% match`;
                } else {
                  return `${image.face_count} face${image.face_count !== 1 ? 's' : ''}`;
                }
              })()}
            </div>
          )}
        </div>
        <div className="p-4">
          <p className="text-sm mb-1"><span className="font-semibold">URN:</span> {image.urn}</p>
          {image.title && <p className="text-sm mb-1"><span className="font-semibold">Title:</span> {image.title}</p>}
          {image.content_keywords.length > 0 && (
            <p className="text-sm mb-1"><span className="font-semibold">Keywords:</span> {image.content_keywords.join(', ')}</p>
          )}
          {image.subject_location.length > 0 && (
            <p className="text-sm mb-1"><span className="font-semibold">Location:</span> {image.subject_location.join(', ')}</p>
          )}
          {image.faces.length > 0 && (
            <div className="mt-2">
              <p className="text-sm font-semibold mb-1">Face Details:</p>
              <div className="text-xs space-y-1">
                {image.faces.map((face, index) => (
                  <div key={index} className="bg-gray-100 p-2 rounded">
                    Face {face.id}: {face.width}×{face.height}px at ({face.left}, {face.top})
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-5">
      <h2 className="text-2xl font-bold mb-3">Face Linking Interface</h2>
      <p className="text-gray-600 mb-5">
        View faces in images of linked persons using V4 method. Face detection is performed automatically and Wikidata images are fetched and cached.
      </p>

      <div className="bg-gray-50 p-5 rounded-lg border border-gray-200 mb-5">
        <div className="flex flex-col">
          <label className="font-semibold mb-2">Select Person (V4 Links Only):</label>
          <select
            value={selectedPerson}
            onChange={(e) => setSelectedPerson(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">
              Select a person... ({linkedPersons.length} available)
            </option>
            {linkedPersons.map((person) => (
              <option key={person.unified_name} value={person.unified_name}>
                {person.display_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <div className="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}

      {loading && <div className="text-center py-5 text-gray-600">Loading person data and detecting faces...</div>}

      {personData && (
        <div>
          <h3 className="text-xl font-bold mb-5">
            Face Analysis for "{personData.unified_name}"
          </h3>

          {/* Wikidata Images Section */}
          {personData.wikidata_images.length > 0 && (
            <div className="mb-8">
              <h4 className="text-lg font-semibold mb-3">
                Wikidata Reference Images ({personData.wikidata_images.length})
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {personData.wikidata_images.map((wikiImg) => (
                  <div key={wikiImg.entity_id} className="border border-gray-300 rounded-lg overflow-hidden bg-white shadow-sm">
                    {wikiImg.has_image && (
                      <div className="relative">
                        <ImageDisplay
                          src={wikiImg.has_faces ? wikiImg.image_with_faces_url : wikiImg.image_url}
                          alt={`Wikidata image for ${personData.unified_name}`}
                          className="w-full"
                        />
                      </div>
                    )}
                    <div className="p-4">
                      <p className="text-sm mb-2">
                        <span className="font-semibold">Source:</span> Wikidata
                      </p>
                      {wikiImg.face_count > 0 && (
                        <p className="text-sm mb-2 text-blue-600">
                          <span className="font-semibold">Faces detected:</span> {wikiImg.face_count}
                        </p>
                      )}
                      <a 
                        href={wikiImg.wikidata_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="inline-block bg-green-600 text-white px-3 py-1 rounded text-sm font-semibold hover:bg-green-700"
                      >
                        View on Wikidata
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Archive Images with Face Detection */}
          <div className="mb-8">
            <h4 className="text-lg font-semibold mb-3">
              Archive Images with Face Detection ({personData.total_images} images, {personData.total_faces} faces)
            </h4>
            
            {personData.images.length === 0 ? (
              <p className="text-gray-500">No images found for this person.</p>
            ) : (
              <>
                <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg mb-5">
                  <p className="text-sm text-blue-800">
                    <strong>Face Detection:</strong> Red bounding boxes show automatically detected faces. 
                    Face coordinates and dimensions are displayed in the image details below each photo.
                  </p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  {personData.images.map((image, index) => (
                    <ImageWithFaces key={image.urn || index} image={image} personData={personData} />
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Face Similarity Analysis */}
          {personData.face_similarity && (
            <div className="mb-8">
              <h4 className="text-lg font-semibold mb-3">Face Similarity Analysis</h4>
              
              {/* Summary Cards */}
              {personData.face_similarity.summary.total_matches > 0 ? (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
                    <div className="bg-white p-4 rounded border border-gray-300">
                      <div className="text-2xl font-bold text-green-600">
                        {(personData.face_similarity.summary.best_similarity * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-gray-600">Best Match</div>
                    </div>
                    <div className="bg-white p-4 rounded border border-gray-300">
                      <div className="text-2xl font-bold text-blue-600">
                        {(personData.face_similarity.summary.average_similarity * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-gray-600">Average Similarity</div>
                    </div>
                    <div className="bg-white p-4 rounded border border-gray-300">
                      <div className="text-2xl font-bold text-purple-600">
                        {personData.face_similarity.summary.total_matches}
                      </div>
                      <div className="text-sm text-gray-600">Face Matches</div>
                    </div>
                  </div>

                  {/* Similarity Details */}
              <div className="bg-white border border-gray-300 rounded-lg p-4">
                <h5 className="font-semibold mb-3">Face Match Details</h5>
                <div className="bg-blue-50 border border-blue-200 p-3 rounded mb-4">
                  <p className="text-sm text-blue-800">
                    <strong>Face Mapping:</strong> Red boxes = Archive images, Blue boxes = Wikidata images. 
                    Each detected face is numbered starting from 0.
                  </p>
                </div>
                <div className="space-y-3">
                  {personData.face_similarity.similarities.slice(0, 10).map((match, index) => {
                    // Find the archive image and Wikidata image for this match
                    const archiveImage = personData.images.find(img => img.urn === match.archive_urn);
                    const wikidataImage = personData.wikidata_images[match.wikidata_image_index];
                    
                    return (
                      <div key={index} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex-1">
                            <div className="text-sm font-medium mb-1">
                              <span className="inline-block bg-red-100 text-red-800 px-2 py-1 rounded text-xs mr-2">
                                Archive Face {match.archive_face_index}
                              </span>
                              ↔
                              <span className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs ml-2">
                                Wikidata Face {match.wikidata_face_index}
                              </span>
                            </div>
                            {match.archive_urn && (
                              <div className="text-xs text-gray-500 mb-1">
                                Archive URN: {match.archive_urn}
                              </div>
                            )}
                            {archiveImage && archiveImage.title && (
                              <div className="text-xs text-gray-500 mb-1">
                                Archive Title: {archiveImage.title}
                              </div>
                            )}
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="text-right">
                              <div className={`text-lg font-bold ${
                                match.similarity >= 0.8 ? 'text-green-600' :
                                match.similarity >= 0.6 ? 'text-yellow-600' : 'text-red-600'
                              }`}>
                                {(match.similarity * 100).toFixed(1)}%
                              </div>
                              <div className="text-xs text-gray-500">
                                Distance: {match.distance.toFixed(3)}
                              </div>
                            </div>
                            <div className={`px-2 py-1 rounded text-xs font-semibold ${
                              match.similarity >= 0.8 ? 'bg-green-100 text-green-800' :
                              match.similarity >= 0.6 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                            }`}>
                              {match.similarity >= 0.8 ? 'Strong Match' :
                               match.similarity >= 0.6 ? 'Moderate Match' : 'Weak Match'}
                            </div>
                          </div>
                        </div>
                        
                        {/* Visual comparison - show thumbnails if available */}
                        <div className="grid grid-cols-2 gap-4 mt-3">
                          <div className="text-center">
                            <div className="text-xs font-semibold text-red-600 mb-1">Archive Image</div>
                            {archiveImage && (
                              <div className="text-xs text-gray-500">
                                {archiveImage.face_count} face{archiveImage.face_count !== 1 ? 's' : ''} detected
                              </div>
                            )}
                          </div>
                          <div className="text-center">
                            <div className="text-xs font-semibold text-blue-600 mb-1">Wikidata Image</div>
                            {wikidataImage && (
                              <div className="text-xs text-gray-500">
                                {wikidataImage.face_count} face{wikidataImage.face_count !== 1 ? 's' : ''} detected
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  {personData.face_similarity.similarities.length > 10 && (
                    <div className="text-center text-sm text-gray-500 pt-3">
                      ... and {personData.face_similarity.similarities.length - 10} more matches
                    </div>
                  )}
                </div>
              </div>
                </>
              ) : (
                <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                  <h5 className="font-semibold text-yellow-800 mb-2">No Face Matches Found</h5>
                  <p className="text-sm text-yellow-700 mb-2">
                    No face similarities were detected between archive and Wikidata images.
                  </p>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <strong>Archive images with faces:</strong> {personData.images.filter(img => img.face_count > 0).length}
                    </div>
                    <div>
                      <strong>Wikidata images with faces:</strong> {personData.wikidata_images.filter(img => img.face_count > 0).length}
                    </div>
                  </div>
                  {personData.images.filter(img => img.face_count > 0).length === 0 && (
                    <p className="text-sm text-yellow-700 mt-2">
                      <strong>Tip:</strong> No faces detected in archive images. Face detection may need better quality images or different orientations.
                    </p>
                  )}
                  {personData.wikidata_images.filter(img => img.face_count > 0).length === 0 && (
                    <p className="text-sm text-yellow-700 mt-2">
                      <strong>Tip:</strong> No faces detected in Wikidata images. This person may not have face photos in Wikidata.
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Summary Statistics */}
          <div className="bg-gray-50 p-5 rounded-lg border border-gray-200">
            <h4 className="text-lg font-semibold mb-3">Summary</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="bg-white p-3 rounded border">
                <div className="text-2xl font-bold text-blue-600">{personData.total_images}</div>
                <div className="text-sm text-gray-600">Archive Images</div>
              </div>
              <div className="bg-white p-3 rounded border">
                <div className="text-2xl font-bold text-red-600">{personData.total_faces}</div>
                <div className="text-sm text-gray-600">Detected Faces</div>
              </div>
              <div className="bg-white p-3 rounded border">
                <div className="text-2xl font-bold text-green-600">{personData.wikidata_images.length}</div>
                <div className="text-sm text-gray-600">Wikidata Images</div>
              </div>
              <div className="bg-white p-3 rounded border">
                <div className="text-2xl font-bold text-purple-600">{personData.wikidata_links.length}</div>
                <div className="text-sm text-gray-600">Wikidata Links</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default FaceLinking;