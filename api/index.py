# api/index.py

from http.server import BaseHTTPRequestHandler
import json
import subprocess
import os

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body)

        url = data.get('url')

        if not url:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing YouTube URL'}).encode())
            return

        try:
            yt_dlp_path = os.path.join(os.getcwd(), 'bin', 'yt-dlp')
            python_path = os.environ.get('PYTHON_BIN', 'python3')

            if not os.path.isfile(yt_dlp_path):
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'yt-dlp binary not found'}).encode())
                return

            command = [python_path, yt_dlp_path, '-F', url, '--print-json']
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if result.returncode != 0:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'yt-dlp error', 'details': result.stderr.decode()}).encode())
                return

            data = json.loads(result.stdout.decode())
            formats = [
                {
                    'format_id': f['format_id'],
                    'ext': f['ext'],
                    'acodec': f.get('acodec'),
                    'vcodec': f.get('vcodec'),
                    'format_note': f.get('format_note'),
                    'resolution': f.get('resolution')
                }
                for f in data.get('formats', [])
            ]

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'title': data['title'], 'formats': formats}).encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Exception occurred', 'details': str(e)}).encode())
