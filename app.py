import flask
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import defaultdict
import requests
import sys
from collections import deque
import itertools

app = Flask(__name__)

def extract_form_details(form):
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
        input_type = input_tag.get('type', 'text')
        input_name = input_tag.get('name', '')
        input_value = input_tag.get('value', '')
        
        input_details = {
            'type': input_type,
            'name': input_name,
            'value': input_value
        }
        form_details['inputs'].append(input_details)

    return form_details

def crawl_bfs(url, base_url, max_depth):
    """
    Crawl the given URL up to the specified max_depth using BFS.
    Returns a hierarchical dictionary of the site structure with input details.
    """
    def get_normalized_url(url):
        """Normalize URL to prevent minor variations causing duplicate crawls"""
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc.rstrip('/')}{parsed.path.rstrip('/')}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized

    # Initialize data structures
    visited_urls = set()
    sitemap = {}
    queue = deque([(url, 0)])

    while queue:
        current_url, current_depth = queue.popleft()
        current_url = get_normalized_url(current_url)

        # Skip if depth exceeded or URL already visited
        if current_depth > max_depth or current_url in visited_urls:
            continue

        # Mark URL as visited
        visited_urls.add(current_url)
        print(f"Crawling: {current_url} at depth {current_depth}")

        try:
            response = requests.get(current_url, timeout=50)
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
                    print(f"Found link: {full_link}")

                    if full_link not in visited_urls:
                        queue.append((full_link, current_depth + 1))

        except requests.RequestException as e:
            print(f"Error crawling {current_url}: {e}")
            continue

    return sitemap

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/tree", methods=["POST"])
def tree():
    if request.method == "POST":
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
    render_template("index.html")
#fuzzzzzzzzzzerrrrr



def load_wordlist(filepath):
    """Load words from a wordlist file"""
    try:
        with open(filepath, 'r') as file:
            return [line.strip() for line in file]
    except FileNotFoundError:
        raise ValueError(f"Wordlist file not found: {filepath}")
    except Exception as e:
        raise ValueError(f"Error reading wordlist: {str(e)}")

def fuzz_url(base_url, wordlist):
    """Fuzz the given URL with words from the wordlist"""
    results = []
    
    # Validate base URL
    if 'FUZZ' not in base_url:
        raise ValueError("Base URL must contain 'FUZZ' placeholder")
    # Check if a file was uploaded
    uploaded_file = request.files.get('custom_wordlist')
    if uploaded_file:
        # Save the uploaded file to a temporary location
        temp_filepath = f"./{uploaded_file.filename}"
        uploaded_file.save(temp_filepath)
        # Load wordlist from the uploaded file
        words = load_wordlist(temp_filepath)
    else:
        # Predefined wordlist paths
        wordlist_paths = {
            "common.txt": "/path/to/wordlists/common.txt",
            "big.txt": "/path/to/wordlists/big.txt",
            "dirs.txt": "/path/to/wordlists/dirs.txt"
        }
        
        # Get full path for the selected wordlist
        full_wordlist_path = wordlist_paths.get(wordlist)
        if not full_wordlist_path:
            raise ValueError("Invalid wordlist selected")
        
        # Load wordlist
        try:
            words = load_wordlist(full_wordlist_path)
        except ValueError as e:
            raise ValueError(str(e))

    # Fuzz URLs
    for word in words:
        fuzzed_url = base_url.replace("FUZZ", word)
        try:
            response = requests.get(fuzzed_url, timeout=10)
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

@app.route("/fuzzer", methods=["GET", "POST"])
def fuzzer():
    """Route to handle URL fuzzing"""
    if request.method == "POST":
        try:
            # Get form data
            base_url = request.form["base_url"]
            wordlist_path = request.form["wordlist_path"]
            
            # Perform fuzzing
            fuzz_results = fuzz_url(base_url, wordlist_path)
            
            # Render results template
            return render_template(
                "fuzzer_results.html", 
                results=fuzz_results, 
                base_url=base_url
            )
        
        except ValueError as e:
            # Handle specific validation errors 
            return render_template(
                "fuzzer.html", 
                error=str(e)
            ), 400
        except Exception as e:
            # Handle unexpected errors
            return render_template(
                "fuzzer.html", 
                error="An unexpected error occurred during fuzzing"
            ), 500
    
    # GET request: render input form
    return render_template("fuzzer.html")

# Optional: Add error handling middleware
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error="Internal server error"), 500




if __name__ == "__main__":
    app.run(debug=True)