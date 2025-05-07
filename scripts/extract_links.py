#!/usr/bin/env python3
"""
Link extraction module for YAML files.
Handles both single link strings and lists of links.
"""

import yaml
import os
import re
from typing import List, Dict, Any, Union

def is_url(text: str) -> bool:
    """Check if a string is a valid URL."""
    if not isinstance(text, str):
        return False
    url_pattern = re.compile(
        r'^(https?:\/\/)?'  # http:// or https://
        r'([a-zA-Z0-9-]+\.)*'  # domain segments
        r'[a-zA-Z0-9-]+'  # domain name
        r'\.[a-zA-Z]{2,}'  # top-level domain
        r'(\/[^\s]*)?$'  # optional path
    )
    return bool(url_pattern.match(text))

def extract_links_from_dict(data: Dict[str, Any]) -> List[str]:
    """
    Recursively extract all links from a dictionary.
    Handles both single link strings and lists of links.
    """
    links = []
    
    for key, value in data.items():
        if key == 'link' and value:
            if isinstance(value, str) and is_url(value):
                links.append(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and is_url(item):
                        links.append(item)
        elif isinstance(value, dict):
            links.extend(extract_links_from_dict(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    links.extend(extract_links_from_dict(item))
                elif isinstance(item, str) and is_url(item):
                    links.append(item)
    
    return links

def extract_links_from_yaml(yaml_file_path: str) -> List[str]:
    """
    Extract all links from a YAML file.
    Returns a list of unique URLs.
    """
    with open(yaml_file_path, 'r', encoding='utf-8') as file:
        try:
            data = yaml.safe_load(file)
            if not data:
                return []
            
            links = extract_links_from_dict(data)
            return list(set(links))  # Return unique links only
        except yaml.YAMLError:
            print(f"Error parsing YAML file: {yaml_file_path}")
            return []

def get_all_yaml_files(directory: str = '.') -> List[str]:
    """Find all YAML files in the given directory and its subdirectories."""
    yaml_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.yaml', '.yml')):
                # Skip files in .git and .github directories
                if '.git' not in root:
                    yaml_files.append(os.path.join(root, file))
    
    return yaml_files

def get_links_from_all_yaml_files(directory: str = '.') -> Dict[str, List[str]]:
    """
    Extract links from all YAML files in the given directory.
    Returns a dictionary mapping file paths to lists of links.
    """
    yaml_files = get_all_yaml_files(directory)
    results = {}
    
    for yaml_file in yaml_files:
        links = extract_links_from_yaml(yaml_file)
        if links:
            results[yaml_file] = links
    
    return results

if __name__ == "__main__":
    # Example usage
    all_files_links = get_links_from_all_yaml_files()
    for file_path, links in all_files_links.items():
        print(f"File: {file_path}")
        for link in links:
            print(f"  - {link}")
        print()