import subprocess
import json
import os

def handler(request, response):
    if request.method != 'POST':
        return response.json({'error': 'Method not allowed'}, status=405)

    body = request.json()
    url = body.get('url')

    if not url:
        return response.json({'error': 'Missing YouTube URL'}, status=400)

    try:
        # Get the yt-dlp binary path and Python path
        yt_dlp_path = os.path.join(os.getcwd(), 'bin', 'yt-dlp')
        python_path = os.environ.get('PYTHON_BIN', 'python3')  # Use environment variable for Python path

        # Use subprocess to execute yt-dlp with Python
        command = [python_path, yt_dlp_path, '-F', url, '--print-json']
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            raise Exception(f"yt-dlp error: {result.stderr.decode('utf-8')}")
        
        # Parse the output from yt-dlp
        data = json.loads(result.stdout.decode('utf-8'))

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
        
        return response.json({'title': data['title'], 'formats': formats})
    
    except Exception as e:
        return response.json({'error': 'Failed to fetch codec details', 'details': str(e)}, status=500)
