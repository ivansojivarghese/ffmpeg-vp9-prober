# api/index.py

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import shutil
# import browser_cookie3
from yt_dlp import YoutubeDL  # Import yt-dlp's YoutubeDL class


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
            url = data.get('url')
        except Exception:
            return self._send_json(400, {'error': 'Invalid JSON'})

        if not url:
            return self._send_json(400, {'error': 'Missing YouTube URL'})

        try:
            # Set up yt-dlp options using the YoutubeDL class
            # ydl_opts = {'dump_single_json': True, 'simulate': True}

            # Path to the exported cookies file
            # cookies_path = os.path.join(os.getcwd(), 'tmp', 'cookies.txt')
            # cookies_path = '/tmp/cookies.txt'

            source_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')  # inside project
            cookies_path = '/tmp/cookies.txt'  # writable during runtime
            shutil.copyfile(source_path, cookies_path)

            # Check if the cookies file exists
            '''
            if not os.path.isfile(cookies_path):
                return self._send_json(500, {'error': 'cookies.txt file not found'})
            '''
            '''
            # Step 1: Extract cookies using browser-cookie3
            cookies = browser_cookie3.chrome()  # For Chrome, or use firefox() for Firefox

            # Step 2: Prepare a dictionary for yt-dlp from the cookies
            cookie_dict = {}
            for cookie in cookies:
                cookie_dict[cookie.name] = cookie.value

            # Step 3: Write the cookies to a temporary file
            cookies_path = '/tmp/cookies.txt'
            with open(cookies_path, 'w') as cookie_file:
                cookie_file.write(json.dumps(cookie_dict))

            print(f"Cookies have been saved to {cookies_path}")
            '''

            ffmpeg_path = os.path.join(os.path.dirname(__file__), '..', 'vercel', 'path0', 'bin', 'ffmpeg')

            # yt-dlp options with cookies
            ydl_opts = {
                'dump_single_json': True,
                # 'simulate': True,
                'cookiefile': cookies_path,  # Use the cookies file stored in /tmp
                'cachedir': False,  # 👈 disables caching to avoid read-only filesystem issues
                'ffmpeg_location': ffmpeg_path,  # 🔥 this is the key line
            }

            with YoutubeDL(ydl_opts) as ydl:
                # Extract video info without downloading
                info = ydl.extract_info(url, download=False)

            
            # Check if 'formats' are available in the extracted data
            formats = [
                {
                    'format_id': f.get('format_id'),
                    'ext': f.get('ext'),
                    'acodec': f.get('acodec'),
                    'vcodec': f.get('vcodec'),
                    'format_note': f.get('format_note'),
                    'resolution': f.get('resolution')
                }
                for f in info.get('formats', [])
            ]

            # Return the video title and available formats
            return self._send_json(200, {
                'title': info.get('title'),
                'formats': formats
            })
            

            # Return full info
            # return self._send_json(200, info)

        except Exception as e:
            return self._send_json(500, {
                'error': 'Exception occurred',
                'details': str(e)
            })


'''
from http.server import BaseHTTPRequestHandler
import json
import subprocess
import os

class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
            url = data.get('url')
        except Exception:
            return self._send_json(400, {'error': 'Invalid JSON'})

        if not url:
            return self._send_json(400, {'error': 'Missing YouTube URL'})

        try:
            yt_dlp_path = os.path.join(os.getcwd(), 'bin', 'yt-dlp')

            print("yt-dlp path exists:", os.path.isfile(yt_dlp_path))
            print("yt-dlp path:", yt_dlp_path)

            if not os.path.isfile(yt_dlp_path):
                return self._send_json(500, {'error': 'yt-dlp binary not found'})

            # Use the standalone binary directly (no need for python3)
            command = [yt_dlp_path, '-F', url, '--print-json']
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if result.returncode != 0:
                return self._send_json(500, {
                    'error': 'yt-dlp error',
                    'details': result.stderr.decode()
                })

            data = json.loads(result.stdout.decode())
            formats = [
                {
                    'format_id': f.get('format_id'),
                    'ext': f.get('ext'),
                    'acodec': f.get('acodec'),
                    'vcodec': f.get('vcodec'),
                    'format_note': f.get('format_note'),
                    'resolution': f.get('resolution')
                }
                for f in data.get('formats', [])
            ]

            return self._send_json(200, {
                'title': data.get('title'),
                'formats': formats
            })

        except Exception as e:
            return self._send_json(500, {
                'error': 'Exception occurred',
                'details': str(e)
            })
'''