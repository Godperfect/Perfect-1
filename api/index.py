from flask import Flask, request, jsonify, send_file
from yt_dlp import YoutubeDL
import os
import tempfile

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Downloader - MrPerfect</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 50px auto;
            max-width: 600px;
            text-align: center;
            position: relative;
            height: 100vh;
        }
        form {
            margin-top: 20px;
        }
        input, select, button {
            padding: 10px;
            margin: 10px 0;
            font-size: 16px;
            width: 90%;
        }
        .message {
            margin-top: 20px;
            color: green;
            font-weight: bold;
        }
        .error {
            color: red;
        }
        .footer {
            margin-top: 40px;
            font-size: 14px;
            color: #555;
            text-align: center;
        }
        .footer a {
            color: #007bff;
            text-decoration: none;
        }
        .footer a:hover {
            text-decoration: underline;
        }
        .download-info {
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <h1>YouTube Downloader - MrPerfect</h1>
    <form id="download-form">
        <input type="url" id="url" name="url" placeholder="Enter YouTube URL" required>
        <select id="choice" name="choice">
            <option value="video">Download Video</option>
            <option value="audio">Download Audio</option>
        </select>
        <button type="submit">Download</button>
    </form>

    <div id="message"></div>

    <div id="download-info" class="download-info"></div>

    <div class="footer">
        <p>Thank you for using MrPerfect site to download content.</p>
        <p><strong>Terms and Conditions:</strong></p>
        <p>By using this website, you agree to our terms and conditions. The content available for download is for personal use only. Redistribution or commercial use of the downloaded content is prohibited.</p>
        <p><strong>Copyright Notice:</strong></p>
        <p>The website and its contents are protected by copyright law. All rights are reserved by MrPerfect. Unauthorized use of this content is prohibited and may result in legal action. For more details, visit <a href="https://www.mrperfect.com" target="_blank">www.mrperfect.com</a>.</p>
    </div>

    <script>
        document.getElementById('download-form').addEventListener('submit', function(e) {
            e.preventDefault();

            const url = document.getElementById('url').value;
            const choice = document.getElementById('choice').value;

            fetch('/api/start_download', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url: url, choice: choice})
            })
            .then(response => {
                if (response.ok) {
                    return response.blob();
                } else {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Download failed');
                    });
                }
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = 'download.' + (choice === 'video' ? 'mp4' : 'mp3');
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.getElementById('message').textContent = 'Download completed successfully!';
            })
            .catch(error => {
                document.getElementById('message').textContent = error.message;
                document.getElementById('message').classList.add('error');
            });
        });
    </script>
</body>
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
        return file_path, result.get('title', 'Unknown Title')

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
        return file_path, result.get('title', 'Unknown Title')

@app.route('/', methods=['GET'])
def index():
    return HTML_TEMPLATE

@app.route('/api/start_download', methods=['POST'])
def start_download():
    data = request.get_json()
    link = data.get('url')
    choice = data.get('choice')

    if not link or not choice:
        return jsonify({'success': False, 'error': "Invalid input. Please try again."}), 400

    try:
        if choice == 'video':
            file_path, title = download_video(link)
        elif choice == 'audio':
            file_path, title = download_audio(link)
        else:
            return jsonify({'success': False, 'error': "Invalid choice!"}), 400

        return send_file(file_path, as_attachment=True, download_name=f"{title}.{'mp4' if choice == 'video' else 'mp3'}")
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
