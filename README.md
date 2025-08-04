# VABiKo Demo Application

A Flask backend with React frontend for demonstrating VABiKo archive features, including face recognition and Wikidata integration.

## Configuration

The application uses `config.py` to manage data directory paths and settings.

### Data Directory Configuration

Edit `config.py` to point to your data directories:

```python
# Data directory paths
ARCHIVE_BASE = "/path/to/your/data/clean/export_jpg"
ENTITIES_FILE = "/path/to/your/data/clean/export_model/vabiko_entities.json"
```

### Environment Variables

You can also configure paths using environment variables:

```bash
export VABIKO_ARCHIVE_BASE="/path/to/your/archive"
export VABIKO_ENTITIES_FILE="/path/to/your/entities.json"
export FLASK_PORT=5000
export FLASK_DEBUG=True
```

## Setup

### Backend (Flask)

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

For face recognition support, you may need system dependencies:
```bash
sudo apt-get update
sudo apt-get install python3-dev cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev
```

Or use the provided installation script:
```bash
python install_face_detection.py
```

2. Configure data paths in `config.py` or set environment variables

3. Start the Flask server:
```bash
python app.py
```

The backend will run on `http://localhost:5000` (or the configured port)

### Frontend (React)

1. Install Node.js dependencies:
```bash
npm install
```

2. Start the React development server:
```bash
npm start
```

The frontend will run on `http://localhost:3000`

## Usage

1. Start both backend and frontend servers
2. Open `http://localhost:3000` in your browser
3. Select an interface from the dropdown:
   - **Archive Browser**: Enter URNs to view images and metadata
   - **People Browser**: Browse images by depicted persons or photographers
   - **Person Linking**: View unified person names with Wikidata links
   - **Face Linking**: Analyze faces in images with person linking and Wikidata reference images

### Face Linking Interface

The Face Linking interface provides advanced facial recognition and similarity analysis:

#### Face Detection
- **Automatic face detection** in both archive and Wikidata images
- **Rotation correction**: Tests original, 90° clockwise, and 90° counter-clockwise orientations
- **HOG algorithm**: Uses Histogram of Oriented Gradients for face detection
- **Visual indicators**: Red bounding boxes for archive images, blue for Wikidata images

#### Face Recognition & Similarity
- **Deep learning model**: Uses dlib's ResNet-34 CNN trained on ~3 million faces
- **128-dimensional encodings**: Each face converted to unique feature vector
- **Similarity scoring**: Euclidean distance converted to percentage (0-100%)
- **Smart thresholds**: Strong (≥80%), Moderate (60-79%), Weak (<60%)
- **Real-time comparison**: Archive faces matched against Wikidata reference images

#### Technical Details
- **Model**: dlib_face_recognition_resnet_model_v1.dat (22.5 MB)
- **Accuracy**: 99.38% on Labeled Faces in the Wild benchmark
- **Caching**: Wikidata face encodings cached locally for performance
- **Automatic rotation**: Handles rotated images common in historical archives

#### Interface Features
- **Similarity badges**: Shows match percentages directly on images (e.g., "85% match")
- **Detailed analysis**: Face-to-face mapping with similarity scores
- **Diagnostic information**: Clear feedback when no matches found
- **Performance optimized**: Cached encodings and parallel processing

## API Endpoints

### Core Endpoints
- `GET /api/interfaces` - List available demo interfaces
- `GET /api/urn/<urn>` - Get data for a specific URN
- `GET /api/image/<urn>` - Serve image file for a URN
- `GET /api/list` - List available URNs (first 100)

### People and Linking Endpoints
- `GET /api/people/depicted` - List depicted persons with photo counts
- `GET /api/people/photographers` - List photographers with photo counts
- `GET /api/linking/unified-names` - List unified names with filtering options
- `GET /api/linking/unified-name/<name>` - Get detailed person information

### Face Recognition Endpoints
- `GET /api/faces/linked-persons` - List persons with V4 links for face analysis
- `GET /api/faces/person/<name>` - Get face detection data and similarity analysis for a person
- `GET /api/image-with-faces/<urn>` - Serve archive image with red face bounding boxes
- `GET /api/wikidata-image/<entity_id>` - Serve cached Wikidata image
- `GET /api/wikidata-image-with-faces/<entity_id>` - Serve Wikidata image with blue face bounding boxes

#### Face Similarity Response Format
The `/api/faces/person/<name>` endpoint returns comprehensive face analysis data:

```json
{
  "unified_name": "Person Name",
  "wikidata_images": [
    {
      "entity_id": "Q123456",
      "face_count": 1,
      "has_faces": true,
      "image_with_faces_url": "/api/wikidata-image-with-faces/Q123456"
    }
  ],
  "images": [
    {
      "urn": "urn:nbn:de:hebis:30:2-123456",
      "face_count": 2,
      "faces": [{"id": 0, "top": 100, "left": 50, "width": 80, "height": 90}]
    }
  ],
  "face_similarity": {
    "summary": {
      "total_matches": 3,
      "best_similarity": 0.87,
      "average_similarity": 0.73,
      "has_strong_match": true
    },
    "similarities": [
      {
        "archive_face_index": 0,
        "wikidata_face_index": 0,
        "similarity": 0.87,
        "distance": 0.13,
        "archive_urn": "urn:nbn:de:hebis:30:2-123456",
        "archive_image_index": 0,
        "wikidata_image_index": 0
      }
    ]
  }
}
```

## Data Source

The application reads from two main data sources:

1. **Archive Images**: Directory structure created by the reorganize script (`ARCHIVE_BASE`)
   - Each subdirectory named with URN (using + format)
   - Contains `image.jpg` and `mets.xml` files

2. **Entities Metadata**: JSON file with parsed metadata (`ENTITIES_FILE`)
   - Contains array of objects with URN, titles, people, keywords, etc.
   - Used for the People Browser interface

3. **Persons CSV**: CSV file with person linking data (`PERSONS_CSV_FILE`)
   - Contains unified names, Wikidata links (V1-V4), and person mappings
   - Used for Person Linking and Face Linking interfaces

4. **Wikidata Cache**: Local cache directory for Wikidata images
   - Automatically created at `wikidata_cache/`
   - Stores fetched person images and metadata

## Configuration Options

All settings in `config.py`:

- `ARCHIVE_BASE`: Path to reorganized image directory
- `ENTITIES_FILE`: Path to entities JSON file  
- `FLASK_DEBUG`: Enable/disable debug mode
- `FLASK_PORT`: Server port (default: 5000)
- `FLASK_HOST`: Server host (default: 127.0.0.1)
- `MAX_URNS_LIST`: Max URNs returned by list endpoint (default: 100)
