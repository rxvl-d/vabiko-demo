#!/usr/bin/env python3
"""
Flask backend for VABiKo demo application.
Provides endpoints for browsing the image archive and serving metadata.
"""

import os
import json
import csv
import ast
import logging
from pathlib import Path
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from collections import defaultdict
import xml.etree.ElementTree as ET
import xml.dom.minidom
from config import ARCHIVE_BASE, ENTITIES_FILE, PERSONS_CSV_FILE, FLASK_DEBUG, FLASK_PORT, FLASK_HOST, MAX_URNS_LIST
from wikidata_cache import WikidataImageCache
from face_detection import FaceDetectionSystem

app = Flask(__name__)
CORS(app)

# Configure logging
if not app.debug:
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.DEBUG)

# Initialize face detection and Wikidata cache systems
face_detector = FaceDetectionSystem()
wikidata_cache = WikidataImageCache()

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
        },
        {
            'id': 'face_linking',
            'name': 'Face Linking',
            'description': 'View faces in images with person linking and Wikidata integration'
        },
        {
            'id': 'face_similarity',
            'name': 'Face Similarity',
            'description': 'Find faces that are similar to each other across all archive images'
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

@app.route('/api/image-with-faces/<path:urn>')
def get_image_with_faces(urn):
    """Serve image with face detection bounding boxes"""
    urn_dir = find_urn_directory(urn)
    
    if not urn_dir:
        return jsonify({'error': f'URN not found: {urn}'}), 404
    
    image_path = urn_dir / 'image.jpg'
    if not image_path.exists():
        return jsonify({'error': f'Image not found for URN: {urn}'}), 404
    
    # Get faces and image with bounding boxes
    result = face_detector.get_faces_with_boxes(image_path)
    
    if result['image_with_boxes']:
        from flask import Response
        return Response(result['image_with_boxes'], mimetype='image/jpeg')
    else:
        # Fallback to original image if face detection fails
        return send_file(str(image_path), mimetype='image/jpeg')

@app.route('/api/wikidata-image/<path:entity_id>')
def get_wikidata_image(entity_id):
    """Serve cached Wikidata image for entity"""
    wikidata_url = f"https://www.wikidata.org/wiki/{entity_id}"
    
    # Get cached image path
    image_path = wikidata_cache.get_cached_image_path(wikidata_url)
    
    if image_path and image_path.exists():
        # Determine mimetype from file extension
        mimetype = 'image/jpeg'
        if str(image_path).lower().endswith('.png'):
            mimetype = 'image/png'
        elif str(image_path).lower().endswith('.gif'):
            mimetype = 'image/gif'
        elif str(image_path).lower().endswith('.webp'):
            mimetype = 'image/webp'
        
        return send_file(str(image_path), mimetype=mimetype)
    else:
        return jsonify({'error': f'Image not found for entity: {entity_id}'}), 404

@app.route('/api/wikidata-image-with-faces/<path:entity_id>')
def get_wikidata_image_with_faces(entity_id):
    """Serve Wikidata image with face detection bounding boxes"""
    wikidata_url = f"https://www.wikidata.org/wiki/{entity_id}"
    
    # Get cached image path
    image_path = wikidata_cache.get_cached_image_path(wikidata_url)
    
    if image_path and image_path.exists():
        # Create image URL for face detection
        image_url = f"http://localhost:{FLASK_PORT}/api/wikidata-image/{entity_id}"
        
        # Get image with face bounding boxes
        image_with_boxes = face_detector.create_wikidata_image_with_face_boxes(image_url)
        
        if image_with_boxes:
            from flask import Response
            return Response(image_with_boxes, mimetype='image/jpeg')
        else:
            # Fallback to original image if face detection fails
            return send_file(str(image_path), mimetype='image/jpeg')
    else:
        return jsonify({'error': f'Image not found for entity: {entity_id}'}), 404

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

@app.route('/api/faces/linked-persons')
def get_linked_persons():
    """Get list of persons with V4 links for face linking interface"""
    linked_persons = []
    
    # Filter for depicted persons with V4 links
    for unified_name, person_records in unified_names_index.items():
        if not unified_name.strip():
            continue
        
        # Check if any record is a depicted person with a V4 link
        has_v4_link = False
        total_images = 0
        wikidata_links = set()
        
        for record in person_records:
            if record.get('person_type', '').strip() == 'depicted_person':
                v4_link = record.get('linked_name_v4', '').strip()
                if v4_link:
                    has_v4_link = True
                    wikidata_links.add(v4_link)
                    
                urns = parse_urn_list(record.get('items_with_person', ''))
                total_images += len(urns)
        
        if has_v4_link and total_images > 0:
            linked_persons.append({
                'unified_name': unified_name,
                'image_count': total_images,
                'wikidata_links': list(wikidata_links),
                'display_name': f"{unified_name} ({total_images} images)"
            })
    
    # Sort by image count descending
    linked_persons.sort(key=lambda x: (-x['image_count'], x['unified_name']))
    
    return jsonify({
        'persons': linked_persons,
        'total': len(linked_persons)
    })

@app.route('/api/faces/person/<path:unified_name>')
def get_person_face_data(unified_name):
    """Get face detection data and Wikidata images for a person"""
    person_records = unified_names_index.get(unified_name, [])
    
    if not person_records:
        return jsonify({'error': f'Person not found: {unified_name}'}), 404
    
    # Filter for depicted person records only
    depicted_records = [
        record for record in person_records 
        if record.get('person_type', '').strip() == 'depicted_person'
    ]
    
    if not depicted_records:
        return jsonify({'error': f'No depicted person records found for: {unified_name}'}), 404
    
    # Collect all URNs and Wikidata links
    all_urns = set()
    wikidata_links = set()
    
    for record in depicted_records:
        v4_link = record.get('linked_name_v4', '').strip()
        if v4_link:
            wikidata_links.add(v4_link)
        
        urns = parse_urn_list(record.get('items_with_person', ''))
        all_urns.update(urns)
    
    # Get image data with face detection
    images_with_faces = []
    for urn in all_urns:
        entity = next((e for e in entities_data if e.get('urn') == urn), None)
        if entity and entity.get('image_path'):
            # Get face detection data
            urn_dir = find_urn_directory(urn)
            if urn_dir:
                image_path = urn_dir / 'image.jpg'
                if image_path.exists():
                    face_data = face_detector.get_faces_with_boxes(image_path)
                    
                    images_with_faces.append({
                        'urn': urn,
                        'title': entity.get('title', ''),
                        'content_keywords': entity.get('content_keywords', []),
                        'subject_location': entity.get('subject_location', []),
                        'faces': face_data['faces'],
                        'face_count': int(face_data['face_count']),
                        'has_faces': bool(face_data['face_count'] > 0)
                    })
    
    # Get Wikidata image data
    wikidata_images = []
    wikidata_image_urls = []
    for link in wikidata_links:
        entity_id = wikidata_cache.get_entity_id(link)
        if entity_id:
            # Fetch/cache the image
            image_data = wikidata_cache.fetch_wikidata_image(link)
            if image_data and not image_data.get('error'):
                image_url = f'/api/wikidata-image/{entity_id}'
                full_image_url = f"http://localhost:{FLASK_PORT}{image_url}"
                
                # Get face detection data for this Wikidata image
                wikidata_face_encodings = face_detector.get_face_encodings_from_url(full_image_url)
                
                wikidata_images.append({
                    'entity_id': entity_id,
                    'wikidata_url': link,
                    'image_url': image_url,
                    'image_with_faces_url': f'/api/wikidata-image-with-faces/{entity_id}',
                    'has_image': bool(image_data.get('image_path')),
                    'face_count': int(len(wikidata_face_encodings)),
                    'has_faces': bool(len(wikidata_face_encodings) > 0)
                })
                # Collect full URLs for face similarity analysis
                wikidata_image_urls.append(full_image_url)
    
    # Perform face similarity analysis
    face_similarity_results = {'similarities': [], 'summary': {'total_matches': 0}}
    if images_with_faces and wikidata_image_urls:
        try:
            # Get archive image paths
            archive_image_paths = []
            for img in images_with_faces:
                if img['face_count'] > 0:  # Only analyze images with faces
                    urn_dir = find_urn_directory(img['urn'])
                    if urn_dir:
                        image_path = urn_dir / 'image.jpg'
                        if image_path.exists():
                            archive_image_paths.append(image_path)
            
            if archive_image_paths:
                face_similarity_results = face_detector.analyze_person_face_similarity(
                    archive_image_paths, wikidata_image_urls
                )
                
                # Add URN mapping to similarity results
                for similarity in face_similarity_results.get('similarities', []):
                    arch_idx = similarity['archive_image_index']
                    if arch_idx < len(archive_image_paths):
                        # Find corresponding URN
                        for img in images_with_faces:
                            urn_dir = find_urn_directory(img['urn'])
                            if urn_dir and urn_dir / 'image.jpg' == archive_image_paths[arch_idx]:
                                similarity['archive_urn'] = img['urn']
                                break
        except Exception as e:
            app.logger.error(f"Error in face similarity analysis: {e}")
    
    return jsonify({
        'unified_name': unified_name,
        'wikidata_links': list(wikidata_links),
        'wikidata_images': wikidata_images,
        'images': images_with_faces,
        'total_images': len(images_with_faces),
        'total_faces': sum(img['face_count'] for img in images_with_faces),
        'face_similarity': face_similarity_results
    })

# Face Similarity API endpoints
from process_all_faces import FaceDatabase, FaceProcessor

face_processor = None
face_db = None

def init_face_similarity():
    """Initialize face similarity system"""
    global face_processor, face_db
    try:
        face_processor = FaceProcessor()
        face_db = FaceDatabase()
        return True
    except Exception as e:
        app.logger.error(f"Error initializing face similarity: {e}")
        return False

@app.route('/api/face-similarity/random-face', methods=['GET'])
def get_random_face():
    """Get a random face to start similarity search"""
    if not face_db and not init_face_similarity():
        return jsonify({'error': 'Face similarity system not available'}), 500
    
    try:
        all_faces = face_db.get_all_faces()
        if not all_faces:
            return jsonify({'error': 'No faces available'}), 404
        
        import random
        random_face = random.choice(all_faces)
        
        # Get names for this face's image
        image_names = face_db.get_image_names(random_face['image_urn'])
        
        return jsonify({
            'face': {
                'id': random_face['id'],
                'face_hash': random_face['face_hash'],
                'image_urn': random_face['image_urn'],
                'face_index': random_face['face_index'],
                'face_image_path': random_face['face_image_path'],
                'face_location': {
                    'left': random_face['face_left'],
                    'top': random_face['face_top'],
                    'right': random_face['face_right'],
                    'bottom': random_face['face_bottom']
                }
            },
            'image_names': image_names
        })
    except Exception as e:
        app.logger.error(f"Error getting random face: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/face-similarity/similar/<face_id>', methods=['GET'])
def get_similar_faces(face_id):
    """Get faces similar to the specified face"""
    if not face_processor and not init_face_similarity():
        return jsonify({'error': 'Face similarity system not available'}), 500
    
    try:
        # Get the target face
        all_faces = face_db.get_all_faces()
        target_face = None
        for face in all_faces:
            if face['id'] == int(face_id):
                target_face = face
                break
        
        if not target_face:
            return jsonify({'error': 'Face not found'}), 404
        
        # Find similar faces
        limit = request.args.get('limit', 10, type=int)
        similar_faces = face_processor.find_similar_faces(
            target_face['face_encoding'], 
            limit=limit + 1  # +1 to exclude the target face itself
        )
        
        # Remove the target face from results
        similar_faces = [sf for sf in similar_faces if sf['face']['id'] != int(face_id)][:limit]
        
        # Format results
        results = []
        for similar_face in similar_faces:
            face = similar_face['face']
            results.append({
                'face': {
                    'id': face['id'],
                    'face_hash': face['face_hash'],
                    'image_urn': face['image_urn'],
                    'face_index': face['face_index'],
                    'face_image_path': face['face_image_path'],
                    'face_location': {
                        'left': face['face_left'],
                        'top': face['face_top'],
                        'right': face['face_right'],
                        'bottom': face['face_bottom']
                    }
                },
                'similarity': similar_face['similarity'],
                'distance': similar_face['distance'],
                'image_names': similar_face['image_names']
            })
        
        return jsonify({
            'target_face': {
                'id': target_face['id'],
                'face_hash': target_face['face_hash'],
                'image_urn': target_face['image_urn'],
                'face_index': target_face['face_index'],
                'face_image_path': target_face['face_image_path']
            },
            'target_image_names': face_db.get_image_names(target_face['image_urn']),
            'similar_faces': results,
            'total_found': len(results)
        })
    except Exception as e:
        app.logger.error(f"Error finding similar faces: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/face-similarity/face-image/<face_hash>')
def serve_face_image(face_hash):
    """Serve extracted face image"""
    try:
        face_image_path = Path("extracted_faces") / f"{face_hash}.jpg"
        if face_image_path.exists():
            return send_file(str(face_image_path), mimetype='image/jpeg')
        else:
            return jsonify({'error': 'Face image not found'}), 404
    except Exception as e:
        app.logger.error(f"Error serving face image: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/face-similarity/stats', methods=['GET'])
def get_face_similarity_stats():
    """Get statistics about the face database"""
    if not face_db and not init_face_similarity():
        return jsonify({'error': 'Face similarity system not available'}), 500
    
    try:
        all_faces = face_db.get_all_faces()
        
        # Count unique images
        unique_images = set(face['image_urn'] for face in all_faces)
        
        return jsonify({
            'total_faces': len(all_faces),
            'unique_images': len(unique_images),
            'avg_faces_per_image': len(all_faces) / len(unique_images) if unique_images else 0
        })
    except Exception as e:
        app.logger.error(f"Error getting face similarity stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Load data at startup
    load_entities_data()
    load_persons_data()
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT, host=FLASK_HOST)