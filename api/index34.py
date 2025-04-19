# api/index.py

from http.server import BaseHTTPRequestHandler
import json
import subprocess
import os
import sys
import shutil
# import browser_cookie3
import yt_dlp
from yt_dlp import YoutubeDL  # Import yt-dlp's YoutubeDL class

print("yt-dlp version:", yt_dlp.version.__version__)  # ✅ proper way

def probe_with_ffprobe(stream_url, ffprobe_path="ffprobe"):
    try:
        result = subprocess.run(
            [
                ffprobe_path,
                "-v", "error",
                "-show_entries", "format:stream=index,codec_name,codec_type,codec_long_name,width,height,bit_rate",
                "-of", "json",
                stream_url
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return json.loads(result.stdout)
    except Exception as e:
        print("ffprobe error:", e)
        return None

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
            source_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')  # inside project
            cookies_path = '/tmp/cookies.txt'  # writable during runtime
            try:
                shutil.copyfile(source_path, cookies_path)
            except FileNotFoundError:
                print("Warning: cookies.txt not found. Continuing without cookies.")
                cookies_path = None

            ffmpeg_path = os.path.join(os.path.dirname(__file__), '..', 'vercel', 'path0', 'bin', 'ffmpeg')
            ffprobe_path = os.path.join(os.path.dirname(__file__), '..', 'vercel', 'path0', 'bin', 'ffprobe')

            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'noplaylist': True,
                'extract_flat': False,
                'ignoreerrors': True,
                'nocheckcertificate': True,
                'force_ipv4': True,
                'allow_unplayable_formats': True,
                'format': 'bestaudio/best', # Helps ensure all formats are listed
                'ffmpeg_location': ffmpeg_path,
                'cachedir': False,
            }
            if cookies_path:
                ydl_opts['cookiefile'] = cookies_path

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                m3u8_streams = []
                for f in info.get('formats', []):
                    if f.get('protocol') in ['m3u8_native', 'm3u8']:
                        m3u8_streams.append({
                            'url': f.get('url'),
                            'format_id': f.get('format_id'),
                            'format_note': f.get('format_note'),
                            'resolution': f.get('resolution'),
                            'acodec': f.get('acodec'),
                            'vcodec': f.get('vcodec'),
                            'abr': f.get('abr'),       # Audio bitrate
                            'vbr': f.get('vbr'),       # Video bitrate
                            'width': f.get('width'),
                            'height': f.get('height'),
                            'fps': f.get('fps'),
                        })

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

                return self._send_json(200, {
                    'title': info.get('title'),
                    'formats': formats,
                    'm3u8_streams': m3u8_streams, # Include the m3u8 streams
                })

        except Exception as e:
            return self._send_json(500, {
                'error': 'Exception occurred',
                'details': str(e)
            })