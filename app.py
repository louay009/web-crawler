import flask
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import defaultdict
import requests
import sys
from collections import deque

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

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)