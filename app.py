import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from threading import Timer

app = Flask(__name__)
CORS(app)  # Allow all origins

UPLOAD_FOLDER = 'files'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def delete_file_later(filepath, delay=3600):
    def delete_file():
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Deleted file: {filepath}")
    Timer(delay, delete_file).start()

@app.route('/proxy', methods=['POST'])
def proxy_pdf():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({'error': 'Missing URL'}), 400

        r = requests.get(url, stream=True, timeout=15)
        r.raise_for_status()

        filename = f"{uuid.uuid4()}.pdf"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        delete_file_later(filepath, delay=3600)

        temp_link = request.host_url + f"{UPLOAD_FOLDER}/{filename}"
        return jsonify({'success': True, 'temp_link': temp_link})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/files/<path:filename>', methods=['GET'])
def serve_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
