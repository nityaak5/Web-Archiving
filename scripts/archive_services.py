#!/usr/bin/env python3
"""
Module for integrating with web archiving services.
Currently supports:
- Internet Archive's Wayback Machine
- Archive.today
"""

import requests
import time
import random
from typing import Dict, Optional, Tuple
from bs4 import BeautifulSoup
import urllib.parse

# Constants
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
]

def get_random_user_agent() -> str:
    """Return a random user agent string to avoid rate limits."""
    return random.choice(USER_AGENTS)

def archive_url_wayback(url: str, max_retries: int = 3) -> Tuple[bool, Optional[str]]:
    """
    Archive a URL using Internet Archive's Wayback Machine.
    
    Args:
        url: The URL to archive
        max_retries: Maximum number of retry attempts
    
    Returns:
        Tuple of (success_flag, archived_url_or_none)
    """
    wayback_endpoint = f"https://web.archive.org/save/{url}"
    headers = {'User-Agent': get_random_user_agent()}
    
    for attempt in range(max_retries):
        try:
            response = requests.get(wayback_endpoint, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Extract the archived URL from the response
                archived_url = response.url
                # Convert from playback to archive URL if needed
                if '/web/' in archived_url:
                    return True, archived_url
                
                # If we got a success but no redirect to an archive URL,
                # extract it from the response content
                soup = BeautifulSoup(response.text, 'html.parser')
                for link in soup.find_all('a'):
                    href = link.get('href')
                    if href and '/web/' in href and url in href:
                        return True, f"https://web.archive.org{href}"
                
                # Fallback
                return True, f"https://web.archive.org/web/*/{url}"
            
            elif response.status_code == 429:  # Too Many Requests
                print(f"Rate limited by Wayback Machine. Retrying in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Failed to archive {url} with Wayback Machine. Status code: {response.status_code}")
                return False, None
                
        except requests.RequestException as e:
            print(f"Error archiving {url} with Wayback Machine: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                return False, None
    
    return False, None

def archive_url_archive_today(url: str, max_retries: int = 3) -> Tuple[bool, Optional[str]]:
    """
    Archive a URL using Archive.today.
   
    
    Args:
        url: The URL to archive
        max_retries: Maximum number of retry attempts
    
    Returns:
        Tuple of (success_flag, archived_url_or_none)
    """
    archive_endpoint = "https://archive.today/submit/"
    encoded_url = urllib.parse.quote(url)
    
    headers = {
        'User-Agent': get_random_user_agent(),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    payload = f"url={encoded_url}"
    
    for attempt in range(max_retries):
        try:
            # First, get a session cookie
            session = requests.Session()
            session.get("https://archive.today/", headers=headers, timeout=30)
            
            # Now submit the URL
            response = session.post(
                archive_endpoint, 
                data=payload, 
                headers=headers, 
                timeout=30, 
                allow_redirects=True
            )
            
            # Check if successful (Archive.today usually redirects to the archived page)
            if response.status_code == 200:
                # Try to extract the archived URL from the response
                if 'archive.today' in response.url or 'archive.is' in response.url:
                    return True, response.url
                
                # Parse the response to find the archived URL
                soup = BeautifulSoup(response.text, 'html.parser')
                for link in soup.find_all('a'):
                    href = link.get('href')
                    if href and ('archive.today' in href or 'archive.is' in href) and url in href:
                        return True, href
                
                # If already archived, find the existing archive
                if 'already been saved' in response.text:
                    for link in soup.find_all('a'):
                        href = link.get('href')
                        if href and href.startswith('/') and len(href) > 2:
                            return True, f"https://archive.today{href}"
                
                # Fallback
                return True, f"https://archive.today/{url}"
            
            elif response.status_code == 429:  # Too Many Requests
                print(f"Rate limited by Archive.today. Retrying in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Failed to archive {url} with Archive.today. Status code: {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return False, None
                
        except requests.RequestException as e:
            print(f"Error archiving {url} with Archive.today: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                return False, None
    
    return False, None

def archive_url(url: str) -> Dict[str, Dict[str, str]]:
    """
    Archive a URL using multiple services.
    
    Args:
        url: The URL to archive
    
    Returns:
        Dictionary with results from each archiving service
    """
    results = {}
    
    # Add a delay to avoid rate limits
    time.sleep(random.uniform(1, 3))
    
    # Internet Archive's Wayback Machine
    wayback_success, wayback_url = archive_url_wayback(url)
    results['wayback_machine'] = {
        'success': wayback_success,
        'archived_url': wayback_url if wayback_success else None
    }
    
    # Add a delay between services
    time.sleep(random.uniform(2, 5))
    
    # Archive.today
    archive_today_success, archive_today_url = archive_url_archive_today(url)
    results['archive_today'] = {
        'success': archive_today_success,
        'archived_url': archive_today_url if archive_today_success else None
    }
    
    return results

if __name__ == "__main__":
    # Example usage
    test_url = "https://example.com"
    results = archive_url(test_url)
    
    print(f"Results for {test_url}:")
    for service, result in results.items():
        print(f"  {service}: {'Success' if result['success'] else 'Failed'}")
        if result['success']:
            print(f"    Archived URL: {result['archived_url']}")