"""
Configuration settings for VABiKo Demo Application.

This file contains all the configurable paths and settings for the application.
Modify these values to point to your specific data directories.
"""

import os

# Data directory paths
ARCHIVE_BASE = os.getenv(
    'VABIKO_ARCHIVE_BASE', 
    "/media/rsebastian/Lexar/vabiko/data/clean/export_jpg"
)
"""Path to the directory containing reorganized archive images.
This should point to the output directory of the reorganize_archive.py script.
Each subdirectory should be named with a URN (using + format) and contain:
- image.jpg (the archive image)
- mets.xml (metadata file)
"""

ENTITIES_FILE = os.getenv(
    'VABIKO_ENTITIES_FILE', 
    "/media/rsebastian/Lexar/vabiko/data/clean/export_model/vabiko_entities.json"
)
"""Path to the JSON file containing parsed metadata for all entities.
This file should contain a list of objects with fields like:
- urn: URN identifier
- title: Image title
- depicted_person: List of people depicted
- photographers: List of photographers
- content_keywords: List of keywords
- etc.
"""

PERSONS_CSV_FILE = os.getenv(
    'VABIKO_PERSONS_CSV', 
    "/media/rsebastian/Lexar/vabiko/data/clean/persons.csv"
)
"""Path to the CSV file containing person name mappings and Wikidata links.
This file should contain columns:
- existing_name: Original name from the archive
- unified_name: Cleaned/standardized name
- linked_name: Wikidata link (v1)
- linked_name_v2/v3/v4: Alternative Wikidata links
- items_with_person: List of URNs containing this person
"""

# Flask application settings
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')

# API settings
MAX_URNS_LIST = int(os.getenv('MAX_URNS_LIST', '100'))
"""Maximum number of URNs to return in the /api/list endpoint"""