from flask import Flask
from flask_socketio import SocketIO
import os
from flask_cors import CORS
socketio = SocketIO()

import logging
logging.basicConfig(level=logging.DEBUG)

def create_app():
    """
    Application factory.
    """
    app = Flask(__name__)
    # Initialize extensions
    CORS(app)
    socketio.init_app(app)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload
    app.config['UPLOAD_FOLDER'] = 'uploads'  # Ensure this directory exists

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.fuzzer import fuzzer_bp
    from app.routes.crawl import crawl_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(fuzzer_bp)
    app.register_blueprint(crawl_bp, url_prefix='/crawl')

    return app