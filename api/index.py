from flask import Flask, request, jsonify, send_file
from yt_dlp import YoutubeDL
import os
import tempfile

app = Flask(__name__)

# HTML template (unchanged, you can keep it as is)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
...
</html>
"""

def download_video(link):
    with tempfile.TemporaryDirectory() as temp_dir:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'noplaylist': True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(link, download=True)
        filename = os.listdir(temp_dir)[-1]
        file_path = os.path.join(temp_dir, filename)
        thumbnail = result.get("thumbnail", "")
        title = result.get("title", "Unknown Title")
        return file_path, title, thumbnail, None

def download_audio(link):
    with tempfile.TemporaryDirectory() as temp_dir:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(link, download=True)
        filename = os.listdir(temp_dir)[-1]
        file_path = os.path.join(temp_dir, filename)
        title = result.get("title", "Unknown Title")
        return file_path, title, None, None

@app.route('/', methods=['GET'])
def index():
    return HTML_TEMPLATE

@app.route('/api/start_download', methods=['POST'])
def start_download():
    data = request.get_json()
    link = data.get('url')
    choice = data.get('choice')

    if not link or not choice:
        return jsonify({'success': False, 'error': "Invalid input. Please try again."})

    try:
        if choice == 'video':
            file_path, title, thumbnail, error = download_video(link)
        elif choice == 'audio':
            file_path, title, thumbnail, error = download_audio(link)
        else:
            return jsonify({'success': False, 'error': "Invalid choice!"})

        if file_path:
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'success': False, 'error': error})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Remove the __main__ block as it's not needed for serverless functions
