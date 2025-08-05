import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ImageDisplay from './ImageDisplay';

function FaceSimilarity() {
  const [targetFace, setTargetFace] = useState(null);
  const [similarFaces, setSimilarFaces] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/face-similarity/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const getRandomFace = async () => {
    setLoading(true);
    setError('');
    setSimilarFaces([]);
    
    try {
      const response = await axios.get('/api/face-similarity/random-face');
      setTargetFace(response.data);
      await findSimilarFaces(response.data.face.id);
    } catch (error) {
      console.error('Error getting random face:', error);
      if (error.response?.status === 404) {
        setError('No faces available. Please run the face processing script first.');
      } else {
        setError('Error loading random face');
      }
    } finally {
      setLoading(false);
    }
  };

  const findSimilarFaces = async (faceId) => {
    try {
      const response = await axios.get(`/api/face-similarity/similar/${faceId}?limit=10`);
      setSimilarFaces(response.data.similar_faces);
    } catch (error) {
      console.error('Error finding similar faces:', error);
      setError('Error finding similar faces');
    }
  };

  const selectFace = async (face) => {
    setLoading(true);
    setError('');
    
    try {
      // Set as new target face
      const newTargetFace = {
        face: face.face,
        image_names: face.image_names
      };
      setTargetFace(newTargetFace);
      
      // Find similar faces for this new target
      await findSimilarFaces(face.face.id);
    } catch (error) {
      console.error('Error selecting face:', error);
      setError('Error selecting face');
    } finally {
      setLoading(false);
    }
  };

  const FaceCard = ({ face, isTarget = false, onClick = null }) => {
    const cardClasses = `border rounded-lg overflow-hidden bg-white shadow-sm ${
      isTarget ? 'border-blue-500 border-2' : 'border-gray-300'
    } ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}`;

    return (
      <div className={cardClasses} onClick={onClick}>
        <div className="relative">
          <ImageDisplay
            src={`/api/face-similarity/face-image/${face.face.face_hash}`}
            alt={`Face ${face.face.face_index}`}
            className="w-full object-cover"
            containerHeight="h-32"
          />
          {isTarget && (
            <div className="absolute top-2 left-2 bg-blue-500 text-white px-2 py-1 rounded text-xs font-semibold">
              Target
            </div>
          )}
          {!isTarget && face.similarity !== undefined && (
            <div className={`absolute top-2 right-2 text-white px-2 py-1 rounded text-xs font-semibold ${
              face.similarity >= 0.8 ? 'bg-green-500' :
              face.similarity >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
            }`}>
              {(face.similarity * 100).toFixed(1)}%
            </div>
          )}
        </div>
        <div className="p-3">
          <div className="text-xs text-gray-500 mb-1">
            Face {face.face.face_index} from image
          </div>
          <div 
            className="text-xs font-mono text-blue-600 mb-2 truncate cursor-pointer hover:underline"
            onClick={(e) => {
              e.stopPropagation();
              // Open modal with full source image
              const modal = document.createElement('div');
              modal.className = 'fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4';
              modal.onclick = (e) => {
                if (e.target === e.currentTarget) {
                  document.body.removeChild(modal);
                }
              };
              
              const imageContainer = document.createElement('div');
              imageContainer.className = 'relative max-w-full max-h-full';
              
              const closeButton = document.createElement('button');
              closeButton.innerHTML = '×';
              closeButton.className = 'absolute top-4 right-4 text-white bg-black bg-opacity-50 rounded-full w-8 h-8 flex items-center justify-center hover:bg-opacity-75 z-10';
              closeButton.onclick = () => document.body.removeChild(modal);
              
              const img = document.createElement('img');
              img.src = `/api/image/${encodeURIComponent(face.face.image_urn)}`;
              img.alt = `Source image: ${face.face.image_urn}`;
              img.className = 'max-w-full max-h-full object-contain';
              
              imageContainer.appendChild(closeButton);
              imageContainer.appendChild(img);
              modal.appendChild(imageContainer);
              document.body.appendChild(modal);
            }}
            title="Click to view full source image"
          >
            {face.face.image_urn}
          </div>
          
          {face.image_names && face.image_names.length > 0 && (
            <div className="mb-2">
              <div className="text-xs font-semibold text-gray-700 mb-1">Associated Names:</div>
              <div className="space-y-1">
                {face.image_names.slice(0, 3).map((name, index) => (
                  <div key={index} className="text-xs bg-gray-100 px-2 py-1 rounded">
                    {name.display_name}
                  </div>
                ))}
                {face.image_names.length > 3 && (
                  <div className="text-xs text-gray-500">
                    +{face.image_names.length - 3} more
                  </div>
                )}
              </div>
            </div>
          )}
          
          {!isTarget && face.similarity !== undefined && (
            <div className="text-xs text-gray-500">
              Distance: {face.distance.toFixed(3)}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-5">
      <h2 className="text-2xl font-bold mb-3">Face Similarity</h2>
      <p className="text-gray-600 mb-5">
        Find faces that are similar to each other across all images in the archive. 
        Click "Get Random Face" to start, then click on any similar face to use it as the new target.
      </p>

      {/* Stats Section */}
      {stats && (
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 mb-5">
          <h3 className="font-semibold mb-2">Database Statistics</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            <div className="bg-white p-3 rounded border">
              <div className="text-2xl font-bold text-blue-600">{stats.total_faces}</div>
              <div className="text-sm text-gray-600">Total Faces</div>
            </div>
            <div className="bg-white p-3 rounded border">
              <div className="text-2xl font-bold text-green-600">{stats.unique_images}</div>
              <div className="text-sm text-gray-600">Unique Images</div>
            </div>
            <div className="bg-white p-3 rounded border">
              <div className="text-2xl font-bold text-purple-600">{stats.avg_faces_per_image.toFixed(1)}</div>
              <div className="text-sm text-gray-600">Avg Faces/Image</div>
            </div>
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="mb-5">
        <button
          onClick={getRandomFace}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Loading...' : 'Get Random Face'}
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded mb-5">
          {error}
        </div>
      )}

      {targetFace && (
        <div>
          {/* Target Face Section */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3">Target Face</h3>
            <div className="max-w-xs">
              <FaceCard face={targetFace} isTarget={true} />
            </div>
          </div>

          {/* Similar Faces Section */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3">
              Most Similar Faces ({similarFaces.length} found)
            </h3>
            
            {similarFaces.length === 0 ? (
              <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                <p className="text-yellow-800">No similar faces found in the database.</p>
              </div>
            ) : (
              <>
                <div className="bg-blue-50 border border-blue-200 p-3 rounded mb-4">
                  <p className="text-sm text-blue-800">
                    <strong>Similarity Scores:</strong> Green (≥80%) = Strong match, 
                    Yellow (60-79%) = Moderate match, Red (&lt;60%) = Weak match. 
                    Click on any face to use it as the new target.
                  </p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {similarFaces.map((similarFace, index) => (
                    <FaceCard
                      key={`${similarFace.face.id}-${index}`}
                      face={similarFace}
                      onClick={() => selectFace(similarFace)}
                    />
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Instructions */}
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <h4 className="font-semibold mb-2">How to Use</h4>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>• The target face is shown with a blue border</li>
              <li>• Similar faces are ranked by similarity percentage</li>
              <li>• Click on any similar face to make it the new target</li>
              <li>• Associated names show people linked to that image</li>
              <li>• Distance values: lower = more similar</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

export default FaceSimilarity;