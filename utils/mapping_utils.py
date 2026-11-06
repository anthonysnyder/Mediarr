"""
TMDb ID to directory mapping utilities with artwork availability tracking
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict


# Path to the mapping file
MAPPING_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'tmdb_directory_mapping.json')


def load_directory_mapping() -> Dict:
    """
    Load the mapping file that remembers which TMDb IDs go to which directories
    and tracks artwork availability.

    Returns:
        Dictionary with mapping data, or empty dict if file doesn't exist
    """
    if os.path.exists(MAPPING_FILE):
        try:
            with open(MAPPING_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading mapping file: {e}")
            return {}
    return {}


def save_directory_mapping(mapping: Dict):
    """
    Save the mapping file to remember which TMDb IDs go to which directories
    and artwork availability state.

    Args:
        mapping: Dictionary to save
    """
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(MAPPING_FILE), exist_ok=True)

        # Write atomically so a concurrent reader never sees a half-written file
        tmp_path = f"{MAPPING_FILE}.tmp.{os.getpid()}"
        with open(tmp_path, 'w') as f:
            json.dump(mapping, f, indent=2)
        os.replace(tmp_path, MAPPING_FILE)

        print(f"Saved directory mapping to {MAPPING_FILE}")

    except Exception as e:
        print(f"Error saving mapping file: {e}")


def get_mapped_directory(tmdb_id: int, media_type: str) -> Optional[str]:
    """
    Check if we already know which directory this TMDb ID belongs to.

    Args:
        tmdb_id: TMDb ID
        media_type: 'movie' or 'tv'

    Returns:
        Directory path if found and exists, None otherwise
    """
    mapping = load_directory_mapping()
    key = f"{media_type}_{tmdb_id}"

    if key not in mapping:
        return None

    mapped_dir = mapping[key].get('directory') if isinstance(mapping[key], dict) else mapping[key]

    if mapped_dir and os.path.exists(mapped_dir):
        print(f"Found existing mapping: {key} -> {mapped_dir}")
        return mapped_dir
    elif mapped_dir:
        print(f"Mapped directory no longer exists: {mapped_dir}, removing mapping")
        # Clean up invalid mapping
        del mapping[key]
        save_directory_mapping(mapping)

    return None


def save_mapped_directory(tmdb_id: int, media_type: str, directory_path: str):
    """
    Remember which directory this TMDb ID belongs to for next time.

    Args:
        tmdb_id: TMDb ID
        media_type: 'movie' or 'tv'
        directory_path: Full path to directory
    """
    mapping = load_directory_mapping()
    key = f"{media_type}_{tmdb_id}"

    # Preserve existing data if it exists
    if key in mapping and isinstance(mapping[key], dict):
        mapping[key]['directory'] = directory_path
        mapping[key]['last_checked'] = datetime.now().strftime('%Y-%m-%d')
    else:
        mapping[key] = {
            'directory': directory_path,
            'last_checked': datetime.now().strftime('%Y-%m-%d'),
            'artwork_availability': {}
        }

    save_directory_mapping(mapping)
    print(f"Saved new mapping: {key} -> {directory_path}")


def mark_artwork_unavailable(tmdb_id: int, media_type: str, artwork_type: str):
    """
    Mark that this artwork type is unavailable on TMDb.
    Persists across container restarts.

    Args:
        tmdb_id: TMDb ID
        media_type: 'movie' or 'tv'
        artwork_type: 'backdrop', 'logo', or 'poster'
    """
    mapping = load_directory_mapping()
    key = f"{media_type}_{tmdb_id}"

    if key not in mapping:
        mapping[key] = {
            'artwork_availability': {},
            'last_checked': datetime.now().strftime('%Y-%m-%d')
        }
    elif not isinstance(mapping[key], dict):
        # Migrate old format (just directory string)
        old_dir = mapping[key]
        mapping[key] = {
            'directory': old_dir,
            'artwork_availability': {},
            'last_checked': datetime.now().strftime('%Y-%m-%d')
        }

    if 'artwork_availability' not in mapping[key]:
        mapping[key]['artwork_availability'] = {}

    mapping[key]['artwork_availability'][artwork_type] = False
    mapping[key]['last_checked'] = datetime.now().strftime('%Y-%m-%d')

    save_directory_mapping(mapping)
    print(f"Marked {artwork_type} as unavailable for {key}")


def is_artwork_available(tmdb_id: int, media_type: str, artwork_type: str) -> Optional[bool]:
    """
    Check if we know this artwork type is unavailable on TMDb.

    Args:
        tmdb_id: TMDb ID
        media_type: 'movie' or 'tv'
        artwork_type: 'backdrop', 'logo', or 'poster'

    Returns:
        True if available, False if unavailable, None if unknown
    """
    mapping = load_directory_mapping()
    key = f"{media_type}_{tmdb_id}"

    if key in mapping and isinstance(mapping[key], dict):
        availability = mapping[key].get('artwork_availability', {})
        return availability.get(artwork_type, None)

    return None  # Unknown, need to check TMDb


def reset_artwork_availability(tmdb_id: int, media_type: str, artwork_type: str):
    """
    Allow re-checking TMDb for this artwork type.
    Use this when TMDb might have added new artwork.

    Args:
        tmdb_id: TMDb ID
        media_type: 'movie' or 'tv'
        artwork_type: 'backdrop', 'logo', or 'poster'
    """
    mapping = load_directory_mapping()
    key = f"{media_type}_{tmdb_id}"

    if key in mapping and isinstance(mapping[key], dict):
        if 'artwork_availability' in mapping[key]:
            if artwork_type in mapping[key]['artwork_availability']:
                del mapping[key]['artwork_availability'][artwork_type]
                mapping[key]['last_checked'] = datetime.now().strftime('%Y-%m-%d')
                save_directory_mapping(mapping)
                print(f"Reset availability for {artwork_type} on {key}")


def get_tmdb_id_by_directory(directory_path: str) -> Optional[Dict[str, any]]:
    """
    Reverse lookup: find TMDb ID by directory path.

    Args:
        directory_path: Full path to directory

    Returns:
        Dictionary with 'tmdb_id' and 'media_type' if found, None otherwise
    """
    mapping = load_directory_mapping()

    for key, value in mapping.items():
        if isinstance(value, dict):
            mapped_dir = value.get('directory')
        else:
            # Old format - just the directory string
            mapped_dir = value

        if mapped_dir == directory_path:
            # Parse the key (format: "movie_12345" or "tv_67890")
            parts = key.split('_', 1)
            if len(parts) == 2:
                media_type, tmdb_id_str = parts
                try:
                    return {
                        'tmdb_id': int(tmdb_id_str),
                        'media_type': media_type
                    }
                except ValueError:
                    continue

    return None
