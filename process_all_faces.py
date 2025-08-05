#!/usr/bin/env python3
"""
Face processing script for VABiKo demo.
Detects faces in all images, extracts face images, computes face vectors,
and stores them with traceability to original images and associated names.
"""

from tqdm import tqdm
import os
import json
import csv
import logging
import sqlite3
from pathlib import Path
from PIL import Image
import face_recognition
import numpy as np
from typing import List, Dict, Tuple, Optional
import hashlib
from config import ARCHIVE_BASE, PERSONS_CSV_FILE, ENTITIES_FILE

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FaceDatabase:
    """Manages face data storage and retrieval"""
    
    def __init__(self, db_path: str = "faces.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for face storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create faces table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS faces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                face_hash TEXT UNIQUE NOT NULL,
                image_urn TEXT NOT NULL,
                face_index INTEGER NOT NULL,
                face_left INTEGER NOT NULL,
                face_top INTEGER NOT NULL,
                face_right INTEGER NOT NULL,
                face_bottom INTEGER NOT NULL,
                face_encoding BLOB NOT NULL,
                face_image_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create image_names table for name associations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS image_names (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_urn TEXT NOT NULL,
                unified_name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                UNIQUE(image_urn, unified_name)
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_face_hash ON faces(face_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_image_urn ON faces(image_urn)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_unified_name ON image_names(unified_name)')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def store_face(self, face_data: Dict) -> int:
        """Store a face in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO faces 
                (face_hash, image_urn, face_index, face_left, face_top, face_right, face_bottom, 
                 face_encoding, face_image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                face_data['face_hash'],
                face_data['image_urn'],
                face_data['face_index'],
                face_data['face_left'],
                face_data['face_top'],
                face_data['face_right'],
                face_data['face_bottom'],
                face_data['face_encoding'].tobytes(),
                face_data['face_image_path']
            ))
            face_id = cursor.lastrowid
            conn.commit()
            return face_id
        except Exception as e:
            logger.error(f"Error storing face: {e}")
            return None
        finally:
            conn.close()
    
    def store_image_names(self, image_urn: str, names: List[Dict]):
        """Store name associations for an image"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for name_data in names:
                cursor.execute('''
                    INSERT OR IGNORE INTO image_names (image_urn, unified_name, display_name)
                    VALUES (?, ?, ?)
                ''', (image_urn, name_data['unified_name'], name_data['display_name']))
            conn.commit()
        except Exception as e:
            logger.error(f"Error storing image names: {e}")
        finally:
            conn.close()
    
    def get_all_faces(self) -> List[Dict]:
        """Get all faces from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, face_hash, image_urn, face_index, face_left, face_top, 
                       face_right, face_bottom, face_encoding, face_image_path
                FROM faces
            ''')
            
            faces = []
            for row in cursor.fetchall():
                face = {
                    'id': row[0],
                    'face_hash': row[1],
                    'image_urn': row[2],
                    'face_index': row[3],
                    'face_left': row[4],
                    'face_top': row[5],
                    'face_right': row[6],
                    'face_bottom': row[7],
                    'face_encoding': np.frombuffer(row[8], dtype=np.float64),
                    'face_image_path': row[9]
                }
                faces.append(face)
            
            return faces
        except Exception as e:
            logger.error(f"Error getting faces: {e}")
            return []
        finally:
            conn.close()
    
    def get_image_names(self, image_urn: str) -> List[Dict]:
        """Get names associated with an image"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT unified_name, display_name FROM image_names 
                WHERE image_urn = ?
            ''', (image_urn,))
            
            return [{'unified_name': row[0], 'display_name': row[1]} 
                   for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting image names: {e}")
            return []
        finally:
            conn.close()

class FaceProcessor:
    """Main face processing system"""
    
    def __init__(self):
        self.face_db = FaceDatabase()
        self.face_images_dir = Path("extracted_faces")
        self.face_images_dir.mkdir(exist_ok=True)
        
        # Load entities data
        self.entities_data = self.load_entities_data()
        
        # Load persons data for name mapping
        self.persons_data = self.load_persons_data()
        self.existing_to_unified = {}
        for person in self.persons_data:
            existing_names = person.get('existing_names', '').split('|') if person.get('existing_names') else []
            for existing_name in existing_names:
                if existing_name.strip():
                    self.existing_to_unified[existing_name.strip()] = person['unified_name']
    
    def load_entities_data(self) -> List[Dict]:
        """Load entities JSON data"""
        try:
            with open(ENTITIES_FILE, 'r', encoding='utf-8') as f:
                entities = json.load(f)
            logger.info(f"Loaded {len(entities)} entity records")
            return entities
        except Exception as e:
            logger.error(f"Error loading entities data: {e}")
            return []
    
    def load_persons_data(self) -> List[Dict]:
        """Load persons CSV data"""
        try:
            persons = []
            with open(PERSONS_CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    persons.append(row)
            logger.info(f"Loaded {len(persons)} person records")
            return persons
        except Exception as e:
            logger.error(f"Error loading persons data: {e}")
            return []
    
    def normalize_urn(self, urn: str) -> str:
        """Normalize URN format"""
        return urn.replace(':', '+')
    
    def find_image_path(self, urn: str) -> Optional[Path]:
        """Find the actual image file for a URN"""
        normalized_urn = self.normalize_urn(urn)
        
        # Look for image in archive
        archive_path = Path(ARCHIVE_BASE)
        if not archive_path.exists():
            return None
        
        # Try to find the image directory
        possible_paths = list(archive_path.rglob(f"*{normalized_urn}*"))
        
        for path in possible_paths:
            if path.is_dir():
                # Look for image files in this directory
                image_extensions = ['.jpg', '.jpeg', '.png', '.tif', '.tiff']
                for ext in image_extensions:
                    image_files = list(path.glob(f"*{ext}"))
                    image_files.extend(list(path.glob(f"*{ext.upper()}")))
                    if image_files:
                        return image_files[0]  # Return first found image
        
        return None
    
    def generate_face_hash(self, image_urn: str, face_index: int, face_location: Tuple) -> str:
        """Generate unique hash for a face"""
        face_str = f"{image_urn}_{face_index}_{face_location[0]}_{face_location[1]}_{face_location[2]}_{face_location[3]}"
        return hashlib.md5(face_str.encode()).hexdigest()
    
    def extract_face_image(self, image_path: Path, face_location: Tuple, face_hash: str) -> Optional[str]:
        """Extract face from image and save as separate file"""
        try:
            # Load image
            image = Image.open(image_path)
            
            # Extract face region (face_recognition returns: top, right, bottom, left)
            top, right, bottom, left = face_location
            face_image = image.crop((left, top, right, bottom))
            
            # Save face image
            face_filename = f"{face_hash}.jpg"
            face_path = self.face_images_dir / face_filename
            face_image.save(face_path, "JPEG", quality=95)
            
            return str(face_path)
        except Exception as e:
            logger.error(f"Error extracting face image: {e}")
            return None
    
    def get_names_for_image(self, image_urn: str) -> List[Dict]:
        """Get all names associated with an image URN"""
        names = []
        
        # Find the entity with matching URN
        for entity in self.entities_data:
            if entity.get('urn') == image_urn:
                # Extract depicted persons
                depicted_persons = entity.get('depicted_person', [])
                
                for person_name in depicted_persons:
                    if person_name.strip():
                        # Map to unified name if available
                        unified_name = self.existing_to_unified.get(person_name.strip(), person_name.strip())
                        
                        names.append({
                            'unified_name': unified_name,
                            'display_name': person_name.strip()
                        })
                
                break  # Found the entity, no need to continue
        
        return names
    
    def process_image_file(self, image_path: str, image_urn: str) -> bool:
        """Process a single image file for face detection"""
        try:
            logger.info(f"Processing image: {image_urn} at {image_path}")
            
            if not Path(image_path).exists():
                logger.warning(f"Image file does not exist: {image_path}")
                return False
            
            # Detect faces
            logger.info(f"Detecting faces in: {image_path}")
            
            # Load image for face recognition
            image = face_recognition.load_image_file(image_path)
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(image, model="hog")
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            logger.info(f"Found {len(face_locations)} faces in {image_urn}")
            
            if not face_locations:
                return True  # No faces found, but processing was successful
            
            # Get names associated with this image
            image_names = self.get_names_for_image(image_urn)
            
            # Store image names in database
            if image_names:
                self.face_db.store_image_names(image_urn, image_names)
            
            # Process each face
            for face_index, (face_location, face_encoding) in enumerate(zip(face_locations, face_encodings)):
                # Generate face hash
                face_hash = self.generate_face_hash(image_urn, face_index, face_location)
                
                # Extract face image
                face_image_path = self.extract_face_image(Path(image_path), face_location, face_hash)
                if not face_image_path:
                    continue
                
                # Store face data
                face_data = {
                    'face_hash': face_hash,
                    'image_urn': image_urn,
                    'face_index': face_index,
                    'face_left': face_location[3],    # left
                    'face_top': face_location[0],     # top
                    'face_right': face_location[1],   # right
                    'face_bottom': face_location[2],  # bottom
                    'face_encoding': face_encoding,
                    'face_image_path': face_image_path
                }
                
                face_id = self.face_db.store_face(face_data)
                if face_id:
                    logger.info(f"Stored face {face_index} from {image_urn} with ID {face_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing image {image_urn}: {e}")
            return False

    def process_image(self, image_urn: str) -> bool:
        """Process a single image for face detection"""
        try:
            logger.info(f"Processing image: {image_urn}")
            
            # Find image file
            image_path = self.find_image_path(image_urn)
            if not image_path:
                logger.warning(f"Could not find image file for URN: {image_urn}")
                return False
            
            # Detect faces
            logger.info(f"Detecting faces in: {image_path}")
            
            # Load image for face recognition
            image = face_recognition.load_image_file(str(image_path))
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(image, model="hog")
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            logger.info(f"Found {len(face_locations)} faces in {image_urn}")
            
            if not face_locations:
                return True  # No faces found, but processing was successful
            
            # Get names associated with this image
            image_names = self.get_names_for_image(image_urn)
            
            # Store image names in database
            if image_names:
                self.face_db.store_image_names(image_urn, image_names)
            
            # Process each face
            for face_index, (face_location, face_encoding) in enumerate(zip(face_locations, face_encodings)):
                # Generate face hash
                face_hash = self.generate_face_hash(image_urn, face_index, face_location)
                
                # Extract face image
                face_image_path = self.extract_face_image(image_path, face_location, face_hash)
                if not face_image_path:
                    continue
                
                # Store face data
                face_data = {
                    'face_hash': face_hash,
                    'image_urn': image_urn,
                    'face_index': face_index,
                    'face_left': face_location[3],    # left
                    'face_top': face_location[0],     # top
                    'face_right': face_location[1],   # right
                    'face_bottom': face_location[2],  # bottom
                    'face_encoding': face_encoding,
                    'face_image_path': face_image_path
                }
                
                face_id = self.face_db.store_face(face_data)
                if face_id:
                    logger.info(f"Stored face {face_index} from {image_urn} with ID {face_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing image {image_urn}: {e}")
            return False
    
    def find_similar_faces(self, target_face_encoding: np.ndarray, limit: int = 10) -> List[Dict]:
        """Find faces most similar to the target face"""
        all_faces = self.face_db.get_all_faces()
        
        if not all_faces:
            return []
        
        # Calculate similarities
        similarities = []
        for face in all_faces:
            distance = face_recognition.face_distance([target_face_encoding], face['face_encoding'])[0]
            similarity = 1.0 - distance
            
            # Get names for this face's image
            image_names = self.face_db.get_image_names(face['image_urn'])
            
            similarities.append({
                'face': face,
                'similarity': similarity,
                'distance': distance,
                'image_names': image_names
            })
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Return top matches
        return similarities[:limit]

def main():
    """Main processing function"""
    logger.info("Starting face processing for all images")
    
    processor = FaceProcessor()
    
    # Glob all image files directly
    archive_path = Path(ARCHIVE_BASE)
    if not archive_path.exists():
        logger.error(f"Archive path does not exist: {ARCHIVE_BASE}")
        return
    
    # Find all image.jpg files in urn* directories
    image_files = list(archive_path.glob("urn*/image.jpg"))
    
    if not image_files:
        logger.warning(f"No image.jpg files found in {ARCHIVE_BASE}/urn*/ directories")
        return
    
    logger.info(f"Found {len(image_files)} images to process")
    
    processed_count = 0
    failed_count = 0
    
    for i, image_file in enumerate(tqdm(image_files), 1):
        # Extract URN from directory name (convert + back to :)
        urn = image_file.parent.name.replace('+', ':')
        
        if processor.process_image_file(str(image_file), urn):
            processed_count += 1
        else:
            failed_count += 1
    
    # Get final stats
    all_faces = processor.face_db.get_all_faces()
    faces_found = len(all_faces)
    
    logger.info(f"Processing complete!")
    logger.info(f"Images processed: {processed_count}, Failed: {failed_count}")
    logger.info(f"Total faces detected: {faces_found}")
    logger.info(f"Average faces per image: {faces_found/processed_count:.2f}" if processed_count > 0 else "N/A")

if __name__ == "__main__":
    main()