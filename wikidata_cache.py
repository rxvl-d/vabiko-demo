#!/usr/bin/env python3
"""
Wikidata image fetching and caching system.
"""

import os
import requests
import json
from pathlib import Path
from urllib.parse import urlparse
import hashlib

class WikidataImageCache:
    def __init__(self, cache_dir="wikidata_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.metadata_file = self.cache_dir / "metadata.json"
        self.load_metadata()
    
    def load_metadata(self):
        """Load cached metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}
    
    def save_metadata(self):
        """Save metadata to disk"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def get_entity_id(self, wikidata_url):
        """Extract entity ID from Wikidata URL"""
        if not wikidata_url or 'wikidata.org' not in wikidata_url:
            return None
        return wikidata_url.split('/')[-1]
    
    def fetch_wikidata_image(self, wikidata_url):
        """Fetch image URL from Wikidata entity"""
        entity_id = self.get_entity_id(wikidata_url)
        if not entity_id:
            return None
        
        # Check cache first
        if entity_id in self.metadata:
            cached_data = self.metadata[entity_id]
            if cached_data.get('image_path') and (self.cache_dir / cached_data['image_path']).exists():
                return cached_data
        
        try:
            # Query Wikidata for image
            sparql_query = f"""
            SELECT ?image WHERE {{
              wd:{entity_id} wdt:P18 ?image .
            }}
            LIMIT 1
            """
            
            url = "https://query.wikidata.org/sparql"
            headers = {
                'User-Agent': 'VABiKo-Demo/1.0 (https://example.com/contact)',
                'Accept': 'application/sparql-results+json'
            }
            
            response = requests.get(url, params={'query': sparql_query, 'format': 'json'}, 
                                  headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            bindings = data.get('results', {}).get('bindings', [])
            
            if not bindings:
                # Cache negative result
                self.metadata[entity_id] = {
                    'image_url': None,
                    'image_path': None,
                    'error': 'No image found'
                }
                self.save_metadata()
                return self.metadata[entity_id]
            
            image_url = bindings[0]['image']['value']
            
            # Download and cache the image
            image_data = self.download_image(image_url)
            if image_data:
                # Generate filename
                url_hash = hashlib.md5(image_url.encode()).hexdigest()
                file_ext = self.get_file_extension(image_url)
                filename = f"{entity_id}_{url_hash}{file_ext}"
                image_path = self.cache_dir / filename
                
                # Save image
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                # Update metadata
                self.metadata[entity_id] = {
                    'image_url': image_url,
                    'image_path': filename,
                    'error': None
                }
                self.save_metadata()
                return self.metadata[entity_id]
            
        except Exception as e:
            print(f"Error fetching Wikidata image for {entity_id}: {e}")
            self.metadata[entity_id] = {
                'image_url': None,
                'image_path': None,
                'error': str(e)
            }
            self.save_metadata()
        
        return self.metadata.get(entity_id)
    
    def download_image(self, image_url):
        """Download image from URL"""
        try:
            headers = {
                'User-Agent': 'VABiKo-Demo/1.0 (https://example.com/contact)'
            }
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Error downloading image {image_url}: {e}")
            return None
    
    def get_file_extension(self, url):
        """Get file extension from URL"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        if path.endswith('.jpg') or path.endswith('.jpeg'):
            return '.jpg'
        elif path.endswith('.png'):
            return '.png'
        elif path.endswith('.gif'):
            return '.gif'
        elif path.endswith('.webp'):
            return '.webp'
        else:
            return '.jpg'  # Default
    
    def get_cached_image_path(self, wikidata_url):
        """Get local path to cached image"""
        entity_id = self.get_entity_id(wikidata_url)
        if not entity_id or entity_id not in self.metadata:
            return None
        
        cached_data = self.metadata[entity_id]
        if cached_data.get('image_path'):
            full_path = self.cache_dir / cached_data['image_path']
            if full_path.exists():
                return full_path
        
        return None