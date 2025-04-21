
from http.server import BaseHTTPRequestHandler
import json
import subprocess
import os
import sys
import shutil
# import browser_cookie3
import multiprocessing
import concurrent.futures
import yt_dlp
from yt_dlp import YoutubeDL  # Import yt-dlp's YoutubeDL class


def probe_with_ffprobe(stream_url, ffprobe_path="ffprobe"):
    try:
        result = subprocess.run(
            [
                ffprobe_path,
                "-v", "error",
                "-show_entries", "stream=index,codec_name,codec_long_name,codec_type,profile,level,width,height,bit_rate,pix_fmt,r_frame_rate",
                "-print_format", "json",
                stream_url
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stderr:
            print("ffprobe stderr:", result.stderr)

        return json.loads(result.stdout)
    except Exception as e:
        print("ffprobe error:", e)
        return None


def generate_vp9_codec_string(stream):
    profile_map = {
        "Profile 0": "00",
        "Profile 1": "01",
        "Profile 2": "02",
        "Profile 3": "03"
    }

    # Guess level based on resolution (fallback if ffprobe gives -99)
    def guess_level(width, height):
        if width >= 3840 or height >= 2160:
            return "11"  # Level 5.1
        elif width >= 2560 or height >= 1440:
            return "10"  # Level 5.0
        elif width >= 1920 or height >= 1080:
            return "09"  # Level 4.2
        else:
            return "08"  # Level 4.1 or below

    profile_str = profile_map.get(stream.get("profile", ""), "00")
    level_str = (
        f"{abs(int(stream.get('level'))):02}" if stream.get("level", -99) >= 0
        else guess_level(stream.get("width", 0), stream.get("height", 0))
    )

    # Bit depth from pix_fmt
    pix_fmt = stream.get("pix_fmt", "")
    bit_depth = {
        "yuv420p": "08",
        "yuv420p10le": "10",
        "yuv420p12le": "12"
    }.get(pix_fmt, "08")

    return f"vp09.{profile_str}.{level_str}.{bit_depth}"


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

            # Get cookies from Chrome (you can change to firefox(), edge(), etc.)
            # cj = browser_cookie3.chrome()

            source_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')  # inside project
            cookies_path = '/tmp/cookies.txt'  # writable during runtime

            # Save to cookies.txt
            # cj.save(cookies_path, ignore_discard=True, ignore_expires=True)

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
            ffprobe_path = os.path.join(os.path.dirname(__file__), '..', 'vercel', 'path0', 'bin', 'ffprobe') 

            # yt-dlp options with cookies
            
            ydl_opts = {
                'dump_single_json': True,
                # 'simulate': True,
                'cookiefile': cookies_path,  # Use the cookies file stored in /tmp
                'cachedir': False,  # 👈 disables caching to avoid read-only filesystem issues
                'ffmpeg_location': ffmpeg_path,  # 🔥 this is the key line
                # 'format': 'bestvideo[protocol^=m3u8]+bestaudio/best[protocol^=m3u8]/best'
            }

            with YoutubeDL(ydl_opts) as ydl:
                # Extract video info without downloading
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])

                # Filter formats to only those with VP9 or VP9.x codecs
                vp9_formats = [
                    f for f in formats
                    if f.get('url') and f.get('vcodec', '').lower().startswith('vp9')
                ]

                ffprobe_results = []

                # Function to probe a single format
                def probe_format(f):
                    try:
                        ff_data = probe_with_ffprobe(f['url'], ffprobe_path)

                        # Try to generate VP9 codec string from the first stream
                        streams = ff_data.get("streams", [])
                        vp9_codec = None

                        if streams:
                            vp9_codec = generate_vp9_codec_string(streams[0])  # Always try first stream

                        return {
                            'format_id': f.get('format_id'),
                            'format_note': f.get('format_note'),
                            'ext': f.get('ext'),
                            'ffprobe': ff_data,
                            'vp9_codec': vp9_codec
                        }
                    except Exception as e:
                        return {
                            'format_id': f.get('format_id'),
                            'error': str(e)
                        }

                try:
                    max_workers = min(32, (multiprocessing.cpu_count() or 1) * 5)
                except Exception:
                    max_workers = 10  # Fallback default

                # Run probing concurrently
                with concurrent.futures.ThreadPoolExecutor(max_workers) as executor:
                    ffprobe_results = list(executor.map(probe_format, vp9_formats))

                # Return everything as JSON
                return self._send_json(200, {
                    # 'title': info.get('title'),
                    # 'formats': formats,        # All formats from yt-dlp
                    'ffprobe': ffprobe_results    # Optional detailed info 
                })

            # Return full info
            # return self._send_json(200, info)

            # CUSTOMIZE WHERE NEEDED

        except Exception as e:
            return self._send_json(500, {
                'error': 'Exception occurred',
                'details': str(e)
            })