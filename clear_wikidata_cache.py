#!/usr/bin/env python3
"""
Script to clear the Wikidata cache (both image cache and face encoding cache).
This can be useful for testing or when you want to refresh cached data.
"""

import os
import json
from pathlib import Path
import shutil
import argparse
import sys

def clear_wikidata_image_cache():
    """Clear the Wikidata image cache directory"""
    cache_dir = Path("wikidata_cache")
    
    if cache_dir.exists():
        try:
            # Remove the entire cache directory
            shutil.rmtree(cache_dir)
            print(f"✓ Cleared Wikidata image cache directory: {cache_dir}")
            return True
        except Exception as e:
            print(f"✗ Error clearing image cache directory: {e}")
            return False
    else:
        print(f"ℹ Wikidata image cache directory does not exist: {cache_dir}")
        return True

def clear_wikidata_face_cache():
    """Clear the Wikidata face encodings cache file"""
    cache_file = Path("wikidata_face_cache.json")
    
    if cache_file.exists():
        try:
            # Remove the cache file
            cache_file.unlink()
            print(f"✓ Cleared Wikidata face cache file: {cache_file}")
            return True
        except Exception as e:
            print(f"✗ Error clearing face cache file: {e}")
            return False
    else:
        print(f"ℹ Wikidata face cache file does not exist: {cache_file}")
        return True

def show_cache_stats():
    """Show current cache statistics"""
    print("\n=== Current Cache Status ===")
    
    # Image cache
    cache_dir = Path("wikidata_cache")
    if cache_dir.exists():
        try:
            image_files = list(cache_dir.glob("*"))
            total_size = sum(f.stat().st_size for f in image_files if f.is_file())
            print(f"Image cache: {len(image_files)} files, {total_size / 1024 / 1024:.2f} MB")
        except Exception as e:
            print(f"Image cache: Error reading - {e}")
    else:
        print("Image cache: Directory does not exist")
    
    # Face cache
    cache_file = Path("wikidata_face_cache.json")
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                face_cache = json.load(f)
            file_size = cache_file.stat().st_size
            print(f"Face cache: {len(face_cache)} entries, {file_size / 1024:.2f} KB")
        except Exception as e:
            print(f"Face cache: Error reading - {e}")
    else:
        print("Face cache: File does not exist")

def main():
    parser = argparse.ArgumentParser(
        description="Clear Wikidata cache files and directories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python clear_wikidata_cache.py                    # Clear all caches
  python clear_wikidata_cache.py --images-only      # Clear only image cache
  python clear_wikidata_cache.py --faces-only       # Clear only face cache
  python clear_wikidata_cache.py --stats-only       # Show cache stats only
        """
    )
    
    parser.add_argument("--images-only", action="store_true",
                       help="Clear only the Wikidata image cache directory")
    parser.add_argument("--faces-only", action="store_true", 
                       help="Clear only the face encodings cache file")
    parser.add_argument("--stats-only", action="store_true",
                       help="Show cache statistics without clearing")
    parser.add_argument("--confirm", action="store_true",
                       help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    # Show current stats first
    show_cache_stats()
    
    if args.stats_only:
        return
    
    # Determine what to clear
    clear_images = True
    clear_faces = True
    
    if args.images_only:
        clear_faces = False
    elif args.faces_only:
        clear_images = False
    
    # Confirmation prompt
    if not args.confirm:
        print(f"\n=== About to clear ===")
        if clear_images:
            print("- Wikidata image cache directory")
        if clear_faces:
            print("- Wikidata face encodings cache file")
        
        response = input("\nProceed? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Cancelled.")
            return
    
    # Clear caches
    print(f"\n=== Clearing Caches ===")
    success = True
    
    if clear_images:
        success &= clear_wikidata_image_cache()
    
    if clear_faces: 
        success &= clear_wikidata_face_cache()
    
    if success:
        print("\n✓ All requested caches cleared successfully!")
        
        # Show final stats
        show_cache_stats()
    else:
        print("\n✗ Some errors occurred while clearing caches.")
        sys.exit(1)

if __name__ == "__main__":
    main()