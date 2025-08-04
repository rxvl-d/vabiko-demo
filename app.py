#!/usr/bin/env python3
"""
Flask backend for VABiKo demo application.
Provides endpoints for browsing the image archive and serving metadata.
"""

import os
import json
from pathlib import Path
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from collections import defaultdict
import xml.etree.ElementTree as ET
import xml.dom.minidom

app = Flask(__name__)
CORS(app)

# Configuration
ARCHIVE_BASE = "/media/rsebastian/Lexar/vabiko/data/clean/export_jpg"
ENTITIES_FILE = "/media/rsebastian/Lexar/vabiko/data/clean/export_model/vabiko_entities.json"

# Global data structures for fast lookups
entities_data = []
people_index = defaultdict(list)  # person_name -> [entity_objects]
photographer_index = defaultdict(list)  # photographer_name -> [entity_objects]

def normalize_urn(urn):
    """Normalize URN format (convert : to + for filesystem lookup)"""
    return urn.replace(':', '+')

def find_urn_directory(urn):
    """Find the directory for a given URN (tries both : and + formats)"""
    archive_path = Path(ARCHIVE_BASE)
    
    # Try normalized format first
    normalized_urn = normalize_urn(urn)
    urn_path = archive_path / normalized_urn
    
    if urn_path.exists():
        return urn_path
    
    # Try original format
    urn_path = archive_path / urn
    if urn_path.exists():
        return urn_path
    
    return None

def load_entities_data():
    """Load and index the entities JSON file at startup"""
    global entities_data, people_index, photographer_index
    
    try:
        print(f"Loading entities data from {ENTITIES_FILE}...")
        with open(ENTITIES_FILE, 'r', encoding='utf-8') as f:
            entities_data = json.load(f)
        
        print(f"Loaded {len(entities_data)} entities")
        
        # Build indexes for fast lookups
        for entity in entities_data:
            # Index depicted persons
            for person in entity.get('depicted_person', []):
                if person.strip():
                    people_index[person].append(entity)
            
            # Index photographers
            for photographer in entity.get('photographers', []):
                if photographer.strip():
                    photographer_index[photographer].append(entity)
        
        print(f"Indexed {len(people_index)} depicted persons and {len(photographer_index)} photographers")
        
    except Exception as e:
        print(f"Error loading entities data: {e}")
        entities_data = []

def format_xml(xml_content):
    """Format XML content for display"""
    try:
        root = ET.fromstring(xml_content)
        rough_string = ET.tostring(root, 'unicode')
        reparsed = xml.dom.minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    except:
        return xml_content

@app.route('/api/interfaces')
def get_interfaces():
    """Get list of available demo interfaces"""
    return jsonify([
        {
            'id': 'archive_browser',
            'name': 'Archive Browser',
            'description': 'Browse images and metadata from the VABiKo archive'
        },
        {
            'id': 'people_browser',
            'name': 'People Browser',
            'description': 'Browse images by depicted persons and photographers'
        }
    ])

@app.route('/api/urn/<path:urn>')
def get_urn_data(urn):
    """Get image and metadata for a specific URN"""
    urn_dir = find_urn_directory(urn)
    
    if not urn_dir:
        return jsonify({'error': f'URN not found: {urn}'}), 404
    
    result = {'urn': urn, 'found': True}
    
    # Check for image file
    image_path = urn_dir / 'image.jpg'
    if image_path.exists():
        result['has_image'] = True
        result['image_url'] = f'/api/image/{urn}'
    else:
        result['has_image'] = False
    
    # Check for metadata file
    mets_path = urn_dir / 'mets.xml'
    if mets_path.exists():
        try:
            with open(mets_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            result['has_metadata'] = True
            result['metadata'] = format_xml(xml_content)
        except Exception as e:
            result['has_metadata'] = False
            result['metadata_error'] = str(e)
    else:
        result['has_metadata'] = False
    
    return jsonify(result)

@app.route('/api/image/<path:urn>')
def get_image(urn):
    """Serve image file for a specific URN"""
    urn_dir = find_urn_directory(urn)
    
    if not urn_dir:
        return jsonify({'error': f'URN not found: {urn}'}), 404
    
    image_path = urn_dir / 'image.jpg'
    if not image_path.exists():
        return jsonify({'error': f'Image not found for URN: {urn}'}), 404
    
    return send_file(str(image_path), mimetype='image/jpeg')

@app.route('/api/list')
def list_urns():
    """List available URNs (first 100 for demo purposes)"""
    archive_path = Path(ARCHIVE_BASE)
    
    if not archive_path.exists():
        return jsonify({'error': 'Archive directory not found'}), 404
    
    urns = []
    for item in sorted(archive_path.iterdir()):
        if item.is_dir() and len(urns) < 100:
            # Convert filesystem format back to URN format
            urn = item.name.replace('+', ':')
            urns.append(urn)
    
    return jsonify({'urns': urns, 'total': len(urns)})

@app.route('/api/people/depicted')
def get_depicted_persons():
    """Get list of all depicted persons with photo counts, sorted by count descending"""
    persons_with_counts = []
    for name in people_index.keys():
        if name.strip():
            count = len(people_index[name])
            persons_with_counts.append({
                'name': name,
                'count': count,
                'display_name': f"{name} ({count})"
            })
    
    # Sort by count descending, then by name ascending
    persons_with_counts.sort(key=lambda x: (-x['count'], x['name']))
    
    return jsonify({'persons': persons_with_counts, 'total': len(persons_with_counts)})

@app.route('/api/people/photographers')
def get_photographers():
    """Get list of all photographers with photo counts, sorted by count descending"""
    photographers_with_counts = []
    for name in photographer_index.keys():
        if name.strip():
            count = len(photographer_index[name])
            photographers_with_counts.append({
                'name': name,
                'count': count,
                'display_name': f"{name} ({count})"
            })
    
    # Sort by count descending, then by name ascending
    photographers_with_counts.sort(key=lambda x: (-x['count'], x['name']))
    
    return jsonify({'photographers': photographers_with_counts, 'total': len(photographers_with_counts)})

@app.route('/api/people/depicted/<path:person_name>')
def get_images_by_person(person_name):
    """Get all images featuring a specific depicted person"""
    entities = people_index.get(person_name, [])
    
    results = []
    for entity in entities:
        # Create a summary of the entity with image info
        result = {
            'urn': entity.get('urn'),
            'title': entity.get('title', ''),
            'image_path': entity.get('image_path', ''),
            'content_keywords': entity.get('content_keywords', []),
            'subject_location': entity.get('subject_location', []),
            'creation_date': entity.get('creation_date', {}),
            'has_image': bool(entity.get('image_path'))
        }
        results.append(result)
    
    return jsonify({
        'person': person_name,
        'images': results,
        'total': len(results)
    })

@app.route('/api/people/photographers/<path:photographer_name>')
def get_images_by_photographer(photographer_name):
    """Get all images by a specific photographer"""
    entities = photographer_index.get(photographer_name, [])
    
    results = []
    for entity in entities:
        # Create a summary of the entity with image info
        result = {
            'urn': entity.get('urn'),
            'title': entity.get('title', ''),
            'image_path': entity.get('image_path', ''),
            'content_keywords': entity.get('content_keywords', []),
            'subject_location': entity.get('subject_location', []),
            'creation_date': entity.get('creation_date', {}),
            'has_image': bool(entity.get('image_path'))
        }
        results.append(result)
    
    return jsonify({
        'photographer': photographer_name,
        'images': results,
        'total': len(results)
    })

if __name__ == '__main__':
    # Load entities data at startup
    load_entities_data()
    app.run(debug=True, port=5000)