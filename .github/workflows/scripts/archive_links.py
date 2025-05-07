#!/usr/bin/env python3
"""
Main script to extract and archive links from YAML files.
This script is intended to be run by a GitHub Action whenever YAML files are modified.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Set
import git

from extract_links import get_links_from_all_yaml_files
from archive_services import archive_url

# Constants
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "archive_log.json")

def ensure_log_directory():
    """Create the logs directory if it doesn't exist."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def load_existing_log() -> Dict[str, Any]:
    """Load the existing archive log if it exists, otherwise return an empty dict."""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error loading log file: {LOG_FILE}. Creating a new one.")
    
    return {"archived_links": {}}

def save_log(log_data: Dict[str, Any]):
    """Save the archive log to disk."""
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)

def get_changed_yaml_files() -> Set[str]:
    """
    Get the list of YAML files that have been modified in the last commit.
    Returns an empty set if we can't determine the changed files.
    """
    try:
        repo = git.Repo('.')
        changed_files = set()
        
        # Get the most recent commit
        most_recent_commit = repo.head.commit
        
        # Get all changed files
        for item in most_recent_commit.diff('HEAD~1'):
            if item.a_path.endswith(('.yaml', '.yml')) or item.b_path.endswith(('.yaml', '.yml')):
                if item.a_path:
                    changed_files.add(item.a_path)
                if item.b_path:
                    changed_files.add(item.b_path)
        
        return changed_files
    except Exception as e:
        print(f"Error getting changed files: {e}")
        return set()

def main():
    """Main function to extract and archive links from YAML files."""
    ensure_log_directory()
    log_data = load_existing_log()
    
    # Get all links from YAML files
    all_files_links = get_links_from_all_yaml_files()
    
    # Try to get only changed files
    changed_files = get_changed_yaml_files()
    if changed_files:
        print(f"Found {len(changed_files)} changed YAML files")
        # Filter to only include changed files
        all_files_links = {f: links for f, links in all_files_links.items() if f in changed_files}
    
    # Count total links to be processed
    total_links = sum(len(links) for links in all_files_links.values())
    processed_links = 0
    
    print(f"Found {len(all_files_links)} YAML files with {total_links} links to process")
    
    # Process each file
    for file_path, links in all_files_links.items():
        print(f"Processing {file_path} with {len(links)} links")
        
        for link in links:
            processed_links += 1
            print(f"[{processed_links}/{total_links}] Processing: {link}")
            
            # Skip if already archived successfully
            if link in log_data["archived_links"] and any(
                service["success"] for service in log_data["archived_links"][link]["services"].values()
            ):
                print(f"  Link already archived, skipping")
                continue
            
            # Archive the link
            archive_results = archive_url(link)
            timestamp = datetime.utcnow().isoformat()
            
            # Create or update log entry
            if link not in log_data["archived_links"]:
                log_data["archived_links"][link] = {
                    "original_url": link,
                    "first_seen": timestamp,
                    "files": [file_path],
                    "services": archive_results
                }
            else:
                # Update existing entry
                log_data["archived_links"][link]["last_updated"] = timestamp
                
                # Add file if not already in the list
                if file_path not in log_data["archived_links"][link]["files"]:
                    log_data["archived_links"][link]["files"].append(file_path)
                
                # Update service results
                for service, result in archive_results.items():
                    log_data["archived_links"][link]["services"][service] = result
            
            # Save after each link to avoid losing progress if interrupted
            save_log(log_data)
            
            # Add a small delay to avoid hammering the archiving services
            time.sleep(1)
    
    print(f"Completed archiving {processed_links} links")

if __name__ == "__main__":
    main()