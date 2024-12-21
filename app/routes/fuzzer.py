from flask import Blueprint
from flask import render_template, request
from typing import Dict, List, Optional
import requests
import os




import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)



fuzzer_bp = Blueprint('fuzzer', __name__)

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
                'status_code': response.status_code,  # Limit content to first 200 characters
            })
        except requests.RequestException as e:
            results.append({
                'url': fuzzed_url,
                'error': str(e)
            })
    
    return results


@fuzzer_bp.route("/fuzzer", methods=["GET", "POST"])
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
                filename = os.path.join('uploads', uploaded_file.filename)
                uploaded_file.save(filename)
                words = load_wordlist(filename)
            else:
                # Predefined wordlists (update paths as needed)
                selected_wordlist = request.form.get("wordlist_path", "common")
                selected_wordlist_path = os.path.join('app', selected_wordlist.lstrip('/'))
                if not selected_wordlist or not os.path.exists(selected_wordlist_path):
                    raise ValueError(f"Invalid or missing wordlist {selected_wordlist_path}")
                
                words = load_wordlist(selected_wordlist_path)
            
            # Perform fuzzing
            fuzz_results = fuzz_url(base_url, words)
            
            # Render results template
            return render_template(
                "fuzzer_result.html", 
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
