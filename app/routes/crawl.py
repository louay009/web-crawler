import warnings
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single InsecureRequestWarning from urllib3 needed
warnings.simplefilter('ignore', InsecureRequestWarning)

from flask import Blueprint, jsonify
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from flask import render_template, request

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

crawl_bp = Blueprint('crawl', __name__)


def extract_form_details(form) -> Dict:
    """
    Extract details from a form element
    """
    form_details = {
        'method': form.get('method', 'GET').upper(),
        'action': form.get('action', ''),
        'inputs': []
    }

    # Extract input fields
    for input_tag in form.find_all(['input', 'textarea', 'select']):
        input_details = {
            'type': input_tag.get('type', 'text'),
            'name': input_tag.get('name', ''),
            'value': input_tag.get('value', '')
        }
        form_details['inputs'].append(input_details)

    return form_details

def crawl_bfs(url: str, base_url: str, max_depth: int) -> Dict:
    """
    Crawl the given URL up to the specified max_depth using BFS.
    Returns a hierarchical dictionary of the site structure with input details.
    """
    def get_normalized_url(url: str) -> str:
        """Normalize URL to prevent minor variations causing duplicate crawls"""
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc.rstrip('/')}{parsed.path.rstrip('/')}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized

    # Initialize data structures
    visited_urls = set()
    sitemap = {}
    queue = [(url, 0)]

    while queue:
        current_url, current_depth = queue.pop(0)
        current_url = get_normalized_url(current_url)

        # Skip if depth exceeded or URL already visited
        if current_depth > max_depth or current_url in visited_urls:
            continue

        # Mark URL as visited
        visited_urls.add(current_url)
        logger.info(f"Crawling: {current_url} at depth {current_depth}")

        try:
            # Disable SSL verification for testing (remove in production)
            response = requests.get(current_url, timeout=50, verify=False)
            soup = BeautifulSoup(response.text, "lxml")

            # Initialize an entry for the current URL in the sitemap
            if current_url not in sitemap:
                sitemap[current_url] = {
                    'links': set(), 
                    'depth': current_depth,
                    'forms': [],
                    'queries': []
                }

            # Extract query parameters from URL
            parsed_url = urlparse(current_url)
            if parsed_url.query:
                sitemap[current_url]['queries'] = [
                    {'name': k, 'value': v} 
                    for k, v in [q.split('=') for q in parsed_url.query.split('&')]
                ]

            # Extract form details
            for form in soup.find_all('form'):
                form_details = extract_form_details(form)
                sitemap[current_url]['forms'].append(form_details)

            # Process all links on the page
            for link_tag in soup.find_all("a", href=True):
                link = link_tag['href']
                full_link = get_normalized_url(urljoin(base_url, link))

                # Only process links within the same domain
                if urlparse(full_link).netloc == urlparse(base_url).netloc:
                    sitemap[current_url]['links'].add(full_link)
                    logger.info(f"Found link: {full_link}")

                    if full_link not in visited_urls:
                        queue.append((full_link, current_depth + 1))

        except requests.RequestException as e:
            logger.error(f"Error crawling {current_url}: {e}")
            continue

    return sitemap



@crawl_bp.route("/", methods=["POST"])
def crawl():
    base_url = request.form["base_url"]
    depth = min(int(request.form["depth"]), 5)  # Limit depth to 5

    sitemap = crawl_bfs(base_url, base_url, depth)

    # Convert sets to lists and prepare data for template
    sitemap_processed = {}
    for url, data in sitemap.items():
        sitemap_processed[url] = {
            'links': list(data['links']),
            'depth': data['depth'],
            'forms': data['forms'],
            'queries': data['queries']
        }

    return render_template("tree.html", sitemap=sitemap_processed, base_url=base_url)
