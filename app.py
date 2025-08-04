#!/usr/bin/env python3
"""
Flask backend for VABiKo demo application.
Provides endpoints for browsing the image archive and serving metadata.
"""

import os
import json
import csv
import ast
from pathlib import Path
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from collections import defaultdict
import xml.etree.ElementTree as ET
import xml.dom.minidom
from config import ARCHIVE_BASE, ENTITIES_FILE, PERSONS_CSV_FILE, FLASK_DEBUG, FLASK_PORT, FLASK_HOST, MAX_URNS_LIST

app = Flask(__name__)
CORS(app)

# Global data structures for fast lookups
entities_data = []
people_index = defaultdict(list)  # person_name -> [entity_objects]
photographer_index = defaultdict(list)  # photographer_name -> [entity_objects]

# Person linking data structures
persons_data = []  # Raw CSV data
unified_names_index = defaultdict(list)  # unified_name -> [person_records]
existing_to_unified = {}  # existing_name -> unified_name

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

def load_persons_data():
    """Load and index the persons CSV file at startup"""
    global persons_data, unified_names_index, existing_to_unified
    
    try:
        print(f"Loading persons data from {PERSONS_CSV_FILE}...")
        with open(PERSONS_CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            persons_data = list(reader)
        
        print(f"Loaded {len(persons_data)} person records")
        
        # Build indexes for fast lookups
        for person in persons_data:
            existing_name = person.get('existing_name', '').strip()
            unified_name = person.get('unified_name', '').strip()
            
            if existing_name and unified_name:
                unified_names_index[unified_name].append(person)
                existing_to_unified[existing_name] = unified_name
        
        print(f"Indexed {len(unified_names_index)} unified names from {len(existing_to_unified)} existing names")
        
    except Exception as e:
        print(f"Error loading persons data: {e}")
        persons_data = []

def parse_urn_list(urn_string):
    """Parse the URN list string from CSV (stored as string representation of Python list)"""
    try:
        if urn_string and urn_string.strip():
            return ast.literal_eval(urn_string)
        return []
    except:
        return []

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
        },
        {
            'id': 'person_linking',
            'name': 'Person Linking',
            'description': 'Browse unified person names with Wikidata links and mapping information'
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
        if item.is_dir() and len(urns) < MAX_URNS_LIST:
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

@app.route('/api/linking/unified-names')
def get_unified_names():
    """Get list of unified names with filtering options"""
    has_link = request.args.get('has_link', '')  # 'true', 'false', or ''
    method = request.args.get('method', 'v1')  # v1, v2, v3, v4
    person_type = request.args.get('person_type', '')  # 'depicted_person', 'photographer', or ''
    
    # Map method to column name
    link_column = {
        'v1': 'linked_name',
        'v2': 'linked_name_v2', 
        'v3': 'linked_name_v3',
        'v4': 'linked_name_v4'
    }.get(method, 'linked_name')
    
    unified_names_with_info = []
    
    for unified_name, person_records in unified_names_index.items():
        if not unified_name.strip():
            continue
        
        # Apply person_type filter - check if any record matches the type
        if person_type:
            matching_records = [
                record for record in person_records 
                if record.get('person_type', '').strip() == person_type
            ]
            if not matching_records:
                continue
            # Use only matching records for further processing
            person_records = matching_records
            
        # Check if any record has a link for this method
        has_any_link = any(
            record.get(link_column, '').strip() 
            for record in person_records
        )
        
        # Apply has_link filter
        if has_link == 'true' and not has_any_link:
            continue
        elif has_link == 'false' and has_any_link:
            continue
        
        # Count total images across all existing names for this unified name
        total_images = 0
        for record in person_records:
            urns = parse_urn_list(record.get('items_with_person', ''))
            total_images += len(urns)
        
        unified_names_with_info.append({
            'unified_name': unified_name,
            'has_link': has_any_link,
            'image_count': total_images,
            'existing_names_count': len(person_records),
            'display_name': f"{unified_name} ({total_images} images, {len(person_records)} variants)"
        })
    
    # Sort by image count descending, then by name
    unified_names_with_info.sort(key=lambda x: (-x['image_count'], x['unified_name']))
    
    return jsonify({
        'unified_names': unified_names_with_info,
        'total': len(unified_names_with_info),
        'method': method,
        'has_link_filter': has_link,
        'person_type_filter': person_type
    })

@app.route('/api/linking/unified-name/<path:unified_name>')
def get_unified_name_details(unified_name):
    """Get detailed information about a unified name"""
    method = request.args.get('method', 'v1')
    person_type = request.args.get('person_type', '')
    
    # Map method to column name
    link_column = {
        'v1': 'linked_name',
        'v2': 'linked_name_v2', 
        'v3': 'linked_name_v3',
        'v4': 'linked_name_v4'
    }.get(method, 'linked_name')
    
    person_records = unified_names_index.get(unified_name, [])
    
    if not person_records:
        return jsonify({'error': f'Unified name not found: {unified_name}'}), 404
    
    # Apply person_type filter if specified
    if person_type:
        person_records = [
            record for record in person_records 
            if record.get('person_type', '').strip() == person_type
        ]
        if not person_records:
            return jsonify({'error': f'No records found for unified name "{unified_name}" with person_type "{person_type}"'}), 404
    
    # Collect all existing names and their info
    existing_names = []
    all_urns = set()
    wikidata_links = set()
    
    for record in person_records:
        existing_name = record.get('existing_name', '').strip()
        link = record.get(link_column, '').strip()
        urns = parse_urn_list(record.get('items_with_person', ''))
        
        existing_names.append({
            'existing_name': existing_name,
            'person_type': record.get('person_type', ''),
            'wikidata_link': link,
            'image_count': len(urns),
            'urns': urns
        })
        
        all_urns.update(urns)
        if link:
            wikidata_links.add(link)
    
    # Get image data for all URNs
    images = []
    for urn in all_urns:
        # Find entity data for this URN
        entity = next((e for e in entities_data if e.get('urn') == urn), None)
        if entity:
            images.append({
                'urn': urn,
                'title': entity.get('title', ''),
                'image_path': entity.get('image_path', ''),
                'content_keywords': entity.get('content_keywords', []),
                'subject_location': entity.get('subject_location', []),
                'creation_date': entity.get('creation_date', {}),
                'has_image': bool(entity.get('image_path'))
            })
    
    return jsonify({
        'unified_name': unified_name,
        'method': method,
        'person_type_filter': person_type,
        'existing_names': existing_names,
        'wikidata_links': list(wikidata_links),
        'images': images,
        'total_images': len(images),
        'total_existing_names': len(existing_names)
    })

if __name__ == '__main__':
    # Load data at startup
    load_entities_data()
    load_persons_data()
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT, host=FLASK_HOST)