# VABiKo Demo Application

A Flask backend with React frontend for demonstrating VABiKo archive features.

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
3. Select "Archive Browser" from the dropdown
4. Enter a URN (e.g., `urn:nbn:de:hebis:30:2-586743`) and click Search
5. View the image and metadata side by side

## API Endpoints

- `GET /api/interfaces` - List available demo interfaces
- `GET /api/urn/<urn>` - Get data for a specific URN
- `GET /api/image/<urn>` - Serve image file for a URN
- `GET /api/list` - List available URNs (first 100)

## Data Source

The application reads from two main data sources:

1. **Archive Images**: Directory structure created by the reorganize script (`ARCHIVE_BASE`)
   - Each subdirectory named with URN (using + format)
   - Contains `image.jpg` and `mets.xml` files

2. **Entities Metadata**: JSON file with parsed metadata (`ENTITIES_FILE`)
   - Contains array of objects with URN, titles, people, keywords, etc.
   - Used for the People Browser interface

## Configuration Options

All settings in `config.py`:

- `ARCHIVE_BASE`: Path to reorganized image directory
- `ENTITIES_FILE`: Path to entities JSON file  
- `FLASK_DEBUG`: Enable/disable debug mode
- `FLASK_PORT`: Server port (default: 5000)
- `FLASK_HOST`: Server host (default: 127.0.0.1)
- `MAX_URNS_LIST`: Max URNs returned by list endpoint (default: 100)
