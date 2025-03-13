from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
from lib.apt_parser import AptParser
import io
import gzip

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
        print(f"Proxying request to: {target_url}")
        response = requests.get(
            target_url, 
            headers={'User-Agent': 'APT-Repository-Previewer/1.0'},
            timeout=10
        )
        
        # Pass through the original status code from the upstream server
        status_code = response.status_code
        print(f"Received status code {status_code} from {target_url}")
        
        # Check if the response is a gzipped file
        if target_url.endswith('.gz') and status_code == 200:
            try:
                print(f"Decompressing gzipped content from {target_url}")
                # Decompress the gzipped content
                gzip_content = io.BytesIO(response.content)
                with gzip.GzipFile(fileobj=gzip_content, mode='rb') as f:
                    decompressed_content = f.read().decode('utf-8')
                print(f"Successfully decompressed content from {target_url}")
                return decompressed_content, status_code, {
                    'Content-Type': 'text/plain',
                    'Access-Control-Allow-Origin': '*'
                }
            except Exception as gz_error:
                print(f"Error decompressing content from {target_url}: {str(gz_error)}")
                return jsonify({
                    'error': f'Error decompressing gzipped content: {str(gz_error)}'
                }), 500
        
        return response.text, status_code, {
            'Content-Type': 'text/plain',
            'Access-Control-Allow-Origin': '*'
        }
    except Exception as e:
        print(f"Error proxying request to {target_url}: {str(e)}")
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