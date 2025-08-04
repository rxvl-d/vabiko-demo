# VABiKo Demo Application

A Flask backend with React frontend for demonstrating VABiKo archive features.

## Setup

### Backend (Flask)

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Start the Flask server:
```bash
python app.py
```

The backend will run on `http://localhost:5000`

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

The application reads from the `data/clean/export_jpg` directory structure created by the reorganize script.
