import os
import logging
from typing import Dict, List, Optional
import flask
from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import requests
import urllib3
# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create file handler which logs even debug messages
fh = logging.FileHandler('web_crawler.log')
fh.setLevel(logging.INFO)

# Create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)
# Disable SSL warnings for self-signed or invalid certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
# logging.basicConfig(
#     level=logging.INFO, 
#     format='%(asctime)s - %(levelname)s: %(message)s',
#     handlers=[
#         logging.FileHandler('web_crawler.log'),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload
app.config['UPLOAD_FOLDER'] = 'uploads'  # Ensure this directory exists

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

def load_wordlist(filepath: str) -> List[str]:
    """
    Load words from a wordlist file with enhanced error handling
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            # Strip whitespace and filter out empty lines
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        logger.error(f"Wordlist file not found: {filepath}")
        raise ValueError(f"Wordlist file not found: {filepath}")
    except IOError as e:
        logger.error(f"Error reading wordlist {filepath}: {e}")
        raise ValueError(f"Error reading wordlist: {str(e)}")

def fuzz_url(base_url: str, words: List[str]) -> List[Dict]:
    """
    Fuzz the given URL with words from the wordlist
    """
    # Validate base URL
    if 'FUZZ' not in base_url:
        raise ValueError("Base URL must contain 'FUZZ' placeholder")

    results = []

    # Fuzz URLs
    for word in words:
        # Sanitize word to prevent potential command injection
        safe_word = ''.join(c for c in word if c.isalnum() or c in ['-', '_'])
        
        fuzzed_url = base_url.replace("FUZZ", safe_word)
        try:
            response = requests.get(fuzzed_url, timeout=10, verify=False)
            results.append({
                'url': fuzzed_url,
                'status_code': response.status_code,
                'content': response.text[:200]  # Limit content to first 200 characters
            })
        except requests.RequestException as e:
            results.append({
                'url': fuzzed_url,
                'error': str(e)
            })
    
    return results

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/crawl", methods=["POST"])
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

@app.route("/fuzzer", methods=["GET", "POST"])
def fuzzer():
    """Route to handle URL fuzzing"""
    if request.method == "POST":
        try:
            # Get form data
            base_url = request.form.get("base_url", "")
            
            # Handle file upload
            uploaded_file = request.files.get('custom_wordlist')
            
            if uploaded_file:
                # Save uploaded file
                filename = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
                uploaded_file.save(filename)
                words = load_wordlist(filename)
            else:
                # Predefined wordlists (update paths as needed)
                wordlist_paths = {
                    "common": os.path.join("wordlists", "common.txt"),
                    "big": os.path.join("wordlists", "big.txt"),
                    "dirs": os.path.join("wordlists", "dirs.txt")
                }
                
                selected_wordlist = request.form.get("wordlist_path", "common")
                wordlist_path = wordlist_paths.get(selected_wordlist)
                
                if not wordlist_path or not os.path.exists(wordlist_path):
                    raise ValueError("Invalid or missing wordlist")
                
                words = load_wordlist(wordlist_path)
            
            # Perform fuzzing
            fuzz_results = fuzz_url(base_url, words)
            
            # Render results template
            return render_template(
                "fuzzer_results.html", 
                results=fuzz_results, 
                base_url=base_url
            )
        
        except ValueError as e:
            # Handle specific validation errors 
            logger.warning(f"Fuzzer validation error: {e}")
            return render_template(
                "fuzzer.html", 
                error=str(e)
            ), 400
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected fuzzer error: {e}")
            return render_template(
                "fuzzer.html", 
                error="An unexpected error occurred during fuzzing"
            ), 500
    
    # GET request: render input form
    return render_template("fuzzer.html")

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error="Internal server error"), 500

if __name__ == "__main__":
    # Ensure wordlists directory exists
    os.makedirs("wordlists", exist_ok=True)
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)