# Modified fuzzer.py
from flask import Blueprint, render_template, request, Response
from typing import Dict, List, Optional
import requests
import os
import logging
import json
import threading

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

fuzzer_bp = Blueprint('fuzzer', __name__)

# Store active fuzzing tasks
active_tasks = {}

def load_wordlist(filepath: str) -> List[str]:
    """Load words from a wordlist file with enhanced error handling"""
    logger.info(f"Attempting to load wordlist from: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            words = [line.strip() for line in file if line.strip()]
            logger.info(f"Successfully loaded {len(words)} words from wordlist")
            return words
    except FileNotFoundError:
        logger.error(f"Wordlist file not found: {filepath}")
        raise ValueError(f"Wordlist file not found: {filepath}")
    except IOError as e:
        logger.error(f"Error reading wordlist {filepath}: {e}")
        raise ValueError(f"Error reading wordlist: {str(e)}")

def stream_fuzz_url(task_id: str, base_url: str, words: List[str]):
    """Generator function to stream fuzzing results"""
    logger.info(f"Starting fuzzing with base URL: {base_url}")
    logger.info(f"Total words to process: {len(words)}")
    
    if 'FUZZ' not in base_url:
        logger.error("Base URL missing 'FUZZ' placeholder")
        raise ValueError("Base URL must contain 'FUZZ' placeholder")
    
    for index, word in enumerate(words, 1):
        # Check if task should stop
        if task_id not in active_tasks:
            logger.info(f"Stopping fuzzing task {task_id}")
            break
            
        safe_word = ''.join(c for c in word if c.isalnum() or c in ['-', '_'])
        fuzzed_url = base_url.replace("FUZZ", safe_word)
        logger.debug(f"Processing word {index}/{len(words)}: {safe_word}")
        
        try:
            response = requests.get(fuzzed_url, timeout=10, verify=False)
            result = {
                'url': fuzzed_url,
                'status_code': response.status_code
            }
        except requests.RequestException as e:
            logger.error(f"Request failed for {fuzzed_url}: {str(e)}")
            result = {
                'url': fuzzed_url,
                'error': str(e)
            }
        
        yield f"data: {json.dumps(result)}\n\n"
        
        if index % 100 == 0:
            logger.info(f"Progress: {index}/{len(words)} words processed")

@fuzzer_bp.route("/fuzzer", methods=["GET", "POST"])
def fuzzer():
    logger.info(f"Fuzzer route accessed with method: {request.method}")
    if request.method == "GET":
        return render_template("fuzzer.html")
    return render_template("fuzzer_streaming.html", base_url=request.form.get("base_url", ""))

@fuzzer_bp.route("/stream_fuzz", methods=["GET"])
def stream_fuzz():
    """Route to stream fuzzing results"""
    logger.info("Stream fuzzing started")
    try:
        base_url = request.args.get("base_url")
        logger.info(f"Received base URL: {base_url}")
        
        if not base_url:
            raise ValueError("Base URL is required")

        # Generate unique task ID
        task_id = str(hash(f"{base_url}_{os.urandom(8).hex()}"))
        active_tasks[task_id] = True
        
        selected_wordlist_path = os.path.join('app', 'wordlists', 'common.txt')
        logger.info(f"Using wordlist path: {selected_wordlist_path}")
        
        words = load_wordlist(selected_wordlist_path)
        logger.info(f"Wordlist loaded successfully with {len(words)} entries")
        
        # Send task ID as the first message
        def generate():
            yield f"data: {json.dumps({'task_id': task_id})}\n\n"
            yield from stream_fuzz_url(task_id, base_url, words)
            
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Transfer-Encoding': 'chunked',
                'Connection': 'keep-alive'
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming fuzzer error: {str(e)}", exc_info=True)
        return str(e), 500

@fuzzer_bp.route("/stop_fuzz/<task_id>", methods=["POST"])
def stop_fuzz(task_id):
    """Stop a running fuzzing task"""
    logger.info(f"Stopping fuzzing task: {task_id}")
    if task_id in active_tasks:
        del active_tasks[task_id]
        return {"status": "success", "message": "Fuzzing stopped"}
    return {"status": "error", "message": "Task not found"}, 404