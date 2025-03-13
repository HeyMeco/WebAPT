from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
from lib.apt_parser import AptParser

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('templates', 'index.html')

@app.route('/config')
def config():
    """Return configuration values from environment variables"""
    return jsonify({
        'APTREPO': os.environ.get('APTREPO', '')
    })

@app.route('/proxy')
def proxy():
    """
    Proxy requests to APT repositories to avoid CORS issues
    """
    target_url = request.args.get('url')
    
    if not target_url:
        return jsonify({'error': 'Missing url parameter'}), 400
    
    try:
        response = requests.get(
            target_url, 
            headers={'User-Agent': 'APT-Repository-Previewer/1.0'},
            timeout=10
        )
        
        return response.text, 200, {
            'Content-Type': 'text/plain',
            'Access-Control-Allow-Origin': '*'
        }
    except Exception as e:
        return jsonify({
            'error': f'Error fetching from repository: {str(e)}'
        }), 500

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 