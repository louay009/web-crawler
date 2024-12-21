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

# Ensure upload directory exists



