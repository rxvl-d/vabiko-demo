#!/usr/bin/env python3
"""
Face detection and recognition system for VABiKo images.
"""

import face_recognition
import json
import logging
from pathlib import Path
from PIL import Image, ImageDraw
import io
import base64
import numpy as np
import requests
import tempfile
import os

class FaceDetectionSystem:
    def __init__(self):
        self.face_cache = {}
        self.wikidata_face_cache = {}  # Cache for Wikidata face encodings
        self.wikidata_cache_file = Path("wikidata_face_cache.json")
        self.logger = logging.getLogger(__name__)
        
        # Load existing Wikidata face cache
        self._load_wikidata_cache()
    
    def _load_wikidata_cache(self):
        """Load Wikidata face encodings cache from disk"""
        try:
            if self.wikidata_cache_file.exists():
                with open(self.wikidata_cache_file, 'r') as f:
                    self.wikidata_face_cache = json.load(f)
                self.logger.info(f"Loaded {len(self.wikidata_face_cache)} cached Wikidata face encodings")
            else:
                self.logger.info("No existing Wikidata face cache found")
        except Exception as e:
            self.logger.error(f"Error loading Wikidata face cache: {e}")
            self.wikidata_face_cache = {}
    
    def _save_wikidata_cache(self):
        """Save Wikidata face encodings cache to disk"""
        try:
            with open(self.wikidata_cache_file, 'w') as f:
                json.dump(self.wikidata_face_cache, f, indent=2)
            self.logger.debug("Saved Wikidata face cache to disk")
        except Exception as e:
            self.logger.error(f"Error saving Wikidata face cache: {e}")
    
    def detect_faces(self, image_path):
        """Detect faces in an image with automatic 90-degree rotation correction"""
        try:
            self.logger.info(f"Starting face detection for: {image_path}")
            
            # Check if file exists
            if not Path(image_path).exists():
                self.logger.error(f"File does not exist: {image_path}")
                return []
            
            # Load image with PIL for rotation capabilities
            from PIL import Image as PILImage
            pil_image = PILImage.open(image_path)
            
            # Try face detection on original orientation and both 90-degree rotations
            orientations_to_try = [
                (0, "original"),
                (90, "90° counter-clockwise"), 
                (-90, "90° clockwise")
            ]
            
            best_faces = []
            best_count = 0
            best_orientation = 0
            best_desc = "original"
            
            for rotation, desc in orientations_to_try:
                self.logger.debug(f"Trying {desc} orientation...")
                
                # Apply rotation if needed
                if rotation != 0:
                    rotated_image = pil_image.rotate(rotation, expand=True)
                else:
                    rotated_image = pil_image
                
                # Convert to format face_recognition expects
                import numpy as np
                image_array = np.array(rotated_image)
                
                self.logger.debug(f"Image dimensions for {desc}: {image_array.shape[1]}x{image_array.shape[0]} (WxH)")
                
                # Find face locations using HOG model
                face_locations = face_recognition.face_locations(image_array, model="hog")
                face_count = len(face_locations)
                
                self.logger.info(f"Found {face_count} faces in {desc} orientation")
                
                # Use this orientation if it found more faces
                if face_count > best_count:
                    best_count = face_count
                    best_orientation = rotation
                    best_desc = desc
                    
                    # Convert to our format
                    faces = []
                    for i, (top, right, bottom, left) in enumerate(face_locations):
                        self.logger.debug(f"Face {i}: top={top}, right={right}, bottom={bottom}, left={left}")
                        faces.append({
                            "id": int(i),
                            "top": int(top),
                            "right": int(right), 
                            "bottom": int(bottom),
                            "left": int(left),
                            "width": int(right - left),
                            "height": int(bottom - top)
                        })
                    best_faces = faces
            
            self.logger.info(f"Best result: {best_count} faces found in {best_desc} orientation")
            return best_faces
            
        except Exception as e:
            self.logger.error(f"Exception in face detection for {image_path}: {e}", exc_info=True)
            return []
    
    def create_image_with_face_boxes(self, image_path, faces):
        """Create image with face bounding boxes drawn, applying same rotation as face detection"""
        try:
            self.logger.debug(f"Creating image with face boxes for {len(faces)} faces")
            
            if not faces:
                # No faces, just return original image
                pil_image = Image.open(image_path)
            else:
                # Re-run the orientation detection to get the best orientation
                from PIL import Image as PILImage
                import numpy as np
                
                pil_image = PILImage.open(image_path)
                
                # Try same orientations as in detect_faces
                orientations_to_try = [
                    (0, "original"),
                    (90, "90° counter-clockwise"), 
                    (-90, "90° clockwise")
                ]
                
                best_count = 0
                best_rotation = 0
                
                for rotation, desc in orientations_to_try:
                    if rotation != 0:
                        rotated_image = pil_image.rotate(rotation, expand=True)
                    else:
                        rotated_image = pil_image
                    
                    image_array = np.array(rotated_image)
                    face_locations = face_recognition.face_locations(image_array, model="hog")
                    
                    if len(face_locations) > best_count:
                        best_count = len(face_locations)
                        best_rotation = rotation
                
                # Apply best rotation
                if best_rotation != 0:
                    pil_image = pil_image.rotate(best_rotation, expand=True)
            
            draw = ImageDraw.Draw(pil_image)
            
            # Draw bounding boxes
            for face in faces:
                left = face['left']
                top = face['top'] 
                right = face['right']
                bottom = face['bottom']
                
                # Draw rectangle
                draw.rectangle([(left, top), (right, bottom)], 
                             outline="red", width=3)
                
                # Draw face ID label
                draw.text((left, top - 20), f"Face {face['id']}", 
                         fill="red")
            
            # Convert to bytes for web display
            buffer = io.BytesIO()
            pil_image.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            
            self.logger.debug("Successfully created image with face boxes")
            return buffer.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error creating image with face boxes: {e}", exc_info=True)
            return None
    
    def get_faces_with_boxes(self, image_path):
        """Get faces and create image with bounding boxes"""
        # Check cache first
        cache_key = str(image_path)
        if cache_key in self.face_cache:
            return self.face_cache[cache_key]
        
        faces = self.detect_faces(image_path)
        image_with_boxes = None
        
        if faces:
            image_with_boxes = self.create_image_with_face_boxes(image_path, faces)
        
        result = {
            'faces': faces,
            'face_count': int(len(faces)),
            'image_with_boxes': image_with_boxes
        }
        
        # Cache result
        self.face_cache[cache_key] = result
        return result
    
    def get_face_encodings(self, image_path):
        """Get face encodings for similarity comparison"""
        try:
            self.logger.debug(f"Getting face encodings for: {image_path}")
            
            # Check if file exists
            if not Path(image_path).exists():
                self.logger.error(f"File does not exist: {image_path}")
                return []
            
            # Load image with PIL for rotation capabilities
            from PIL import Image as PILImage
            pil_image = PILImage.open(image_path)
            
            # Try same orientations as in detect_faces
            orientations_to_try = [
                (0, "original"),
                (90, "90° counter-clockwise"), 
                (-90, "90° clockwise")
            ]
            
            best_encodings = []
            best_count = 0
            
            for rotation, desc in orientations_to_try:
                # Apply rotation if needed
                if rotation != 0:
                    rotated_image = pil_image.rotate(rotation, expand=True)
                else:
                    rotated_image = pil_image
                
                # Convert to format face_recognition expects
                image_array = np.array(rotated_image)
                
                # Get face locations and encodings
                face_locations = face_recognition.face_locations(image_array, model="hog")
                face_encodings = face_recognition.face_encodings(image_array, face_locations)
                
                if len(face_encodings) > best_count:
                    best_count = len(face_encodings)
                    best_encodings = face_encodings
            
            self.logger.info(f"Found {len(best_encodings)} face encodings")
            return best_encodings
            
        except Exception as e:
            self.logger.error(f"Exception getting face encodings for {image_path}: {e}")
            return []
    
    def get_face_encodings_from_url(self, image_url):
        """Get face encodings from an image URL (for Wikidata images) with caching"""
        try:
            # Check cache first
            if image_url in self.wikidata_face_cache:
                self.logger.debug(f"Using cached face encodings for URL: {image_url}")
                cached_encodings = self.wikidata_face_cache[image_url]
                # Convert back to numpy arrays if needed
                if cached_encodings and isinstance(cached_encodings[0], list):
                    return [np.array(encoding) for encoding in cached_encodings]
                return cached_encodings
            
            self.logger.debug(f"Getting face encodings from URL: {image_url}")
            
            # Download image to temporary file
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(response.content)
                temp_path = tmp_file.name
            
            try:
                # Get encodings from temporary file
                encodings = self.get_face_encodings(temp_path)
                
                # Cache the results (convert numpy arrays to lists for JSON serialization)
                cacheable_encodings = [encoding.tolist() for encoding in encodings]
                self.wikidata_face_cache[image_url] = cacheable_encodings
                
                # Save cache to disk
                self._save_wikidata_cache()
                
                self.logger.info(f"Cached {len(encodings)} face encodings for URL: {image_url}")
                return encodings
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Exception getting face encodings from URL {image_url}: {e}")
            # Cache empty result to avoid repeated failures
            self.wikidata_face_cache[image_url] = []
            self._save_wikidata_cache()
            return []
    
    def compare_faces(self, archive_encodings, wikidata_encodings, threshold=0.6):
        """Compare faces between archive and Wikidata images"""
        try:
            if not archive_encodings or not wikidata_encodings:
                return []
            
            similarities = []
            
            for i, archive_encoding in enumerate(archive_encodings):
                for j, wikidata_encoding in enumerate(wikidata_encodings):
                    # Calculate face distance (lower is more similar)
                    distance = face_recognition.face_distance([wikidata_encoding], archive_encoding)[0]
                    similarity = 1.0 - distance  # Convert to similarity score
                    
                    # Only include if above threshold
                    if similarity >= threshold:
                        similarities.append({
                            'archive_face_index': int(i),
                            'wikidata_face_index': int(j),
                            'similarity': float(similarity),
                            'distance': float(distance),
                            'is_match': bool(similarity >= threshold)
                        })
            
            # Sort by similarity descending
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            self.logger.info(f"Found {len(similarities)} face matches above threshold {threshold}")
            return similarities
            
        except Exception as e:
            self.logger.error(f"Exception comparing faces: {e}")
            return []
    
    def analyze_person_face_similarity(self, archive_image_paths, wikidata_image_urls):
        """Analyze face similarity between archive images and Wikidata images for a person"""
        try:
            self.logger.info(f"Analyzing face similarity for {len(archive_image_paths)} archive images and {len(wikidata_image_urls)} Wikidata images")
            
            results = {
                'archive_faces': {},
                'wikidata_faces': {},
                'similarities': []
            }
            
            # Store encodings temporarily for comparison (not in results)
            archive_encodings_data = {}
            wikidata_encodings_data = {}
            
            # Get encodings for archive images
            for i, image_path in enumerate(archive_image_paths):
                encodings = self.get_face_encodings(image_path)
                if encodings:
                    results['archive_faces'][str(i)] = {
                        'image_path': str(image_path),
                        'face_count': len(encodings)
                    }
                    archive_encodings_data[str(i)] = encodings
            
            # Get encodings for Wikidata images
            for i, image_url in enumerate(wikidata_image_urls):
                encodings = self.get_face_encodings_from_url(image_url)
                if encodings:
                    results['wikidata_faces'][str(i)] = {
                        'image_url': image_url,
                        'face_count': len(encodings)
                    }
                    wikidata_encodings_data[str(i)] = encodings
            
            # Compare all combinations using the temporary encoding data
            all_similarities = []
            for arch_idx in archive_encodings_data:
                for wiki_idx in wikidata_encodings_data:
                    similarities = self.compare_faces(
                        archive_encodings_data[arch_idx], 
                        wikidata_encodings_data[wiki_idx]
                    )
                    
                    for sim in similarities:
                        sim['archive_image_index'] = int(arch_idx)
                        sim['wikidata_image_index'] = int(wiki_idx)
                        all_similarities.append(sim)
            
            results['similarities'] = all_similarities
            
            # Calculate summary statistics
            if all_similarities:
                best_match = max(all_similarities, key=lambda x: x['similarity'])
                avg_similarity = sum(s['similarity'] for s in all_similarities) / len(all_similarities)
                results['summary'] = {
                    'total_matches': int(len(all_similarities)),
                    'best_similarity': float(best_match['similarity']),
                    'average_similarity': float(avg_similarity),
                    'has_strong_match': bool(best_match['similarity'] >= 0.8)
                }
            else:
                results['summary'] = {
                    'total_matches': 0,
                    'best_similarity': 0.0,
                    'average_similarity': 0.0,
                    'has_strong_match': False
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Exception in face similarity analysis: {e}")
            return {'archive_faces': {}, 'wikidata_faces': {}, 'similarities': [], 'summary': {'total_matches': 0}}
    
    def create_wikidata_image_with_face_boxes(self, image_url):
        """Create Wikidata image with face bounding boxes drawn"""
        try:
            self.logger.debug(f"Creating Wikidata image with face boxes for URL: {image_url}")
            
            # Download image to temporary file
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(response.content)
                temp_path = tmp_file.name
            
            try:
                # Get face detection results
                faces = self.detect_faces(temp_path)
                
                # Load image for drawing
                pil_image = Image.open(temp_path)
                
                # If faces were found, we need to apply the same rotation as used in detection
                if faces:
                    # Re-determine best rotation (same logic as in detect_faces)
                    from PIL import Image as PILImage
                    original_image = PILImage.open(temp_path)
                    
                    orientations_to_try = [
                        (0, "original"),
                        (90, "90° counter-clockwise"), 
                        (-90, "90° clockwise")
                    ]
                    
                    best_count = 0
                    best_rotation = 0
                    
                    for rotation, desc in orientations_to_try:
                        if rotation != 0:
                            rotated_image = original_image.rotate(rotation, expand=True)
                        else:
                            rotated_image = original_image
                        
                        image_array = np.array(rotated_image)
                        face_locations = face_recognition.face_locations(image_array, model="hog")
                        
                        if len(face_locations) > best_count:
                            best_count = len(face_locations)
                            best_rotation = rotation
                    
                    # Apply best rotation
                    if best_rotation != 0:
                        pil_image = original_image.rotate(best_rotation, expand=True)
                
                # Draw bounding boxes
                draw = ImageDraw.Draw(pil_image)
                
                for face in faces:
                    left = face['left']
                    top = face['top'] 
                    right = face['right']
                    bottom = face['bottom']
                    
                    # Draw rectangle (using blue for Wikidata images to distinguish from red archive images)
                    draw.rectangle([(left, top), (right, bottom)], 
                                 outline="blue", width=3)
                    
                    # Draw face ID label
                    draw.text((left, top - 20), f"Face {face['id']}", 
                             fill="blue")
                
                # Convert to bytes for web display
                buffer = io.BytesIO()
                pil_image.save(buffer, format='JPEG', quality=85)
                buffer.seek(0)
                
                self.logger.debug(f"Successfully created Wikidata image with {len(faces)} face boxes")
                return buffer.getvalue()
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Error creating Wikidata image with face boxes: {e}")
            return None