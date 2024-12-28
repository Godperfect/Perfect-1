from flask import Flask, request, render_template_string, jsonify, send_from_directory
import yt_dlp
import os

app = Flask(__name__)

# Directory to store downloaded files temporarily
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

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
        /* Style for the footer with Terms & Conditions */
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

            fetch('/start_download', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url: url, choice: choice})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('message').textContent = data.message;
                    window.location.href = data.download_link; // Automatically download the file

                    // Display the video or audio information
                    const downloadInfo = document.getElementById('download-info');
                    if (data.choice === 'video') {
                        downloadInfo.innerHTML = `
                            <h3>Video: ${data.title}</h3>
                            <img src="${data.thumbnail}" alt="Video Thumbnail" width="200" />
                        `;
                    } else {
                        downloadInfo.innerHTML = `<h3>Audio: ${data.title}</h3>`;
                    }
                } else {
                    document.getElementById('message').textContent = data.error;
                }
            });
        });
    </script>
</body>
</html>
"""

def download_video(link):
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'quiet': True,
            'noplaylist': True,  # Don't download playlists
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(link, download=True)
        filename = os.listdir(DOWNLOAD_FOLDER)[-1]  # Get the last downloaded file
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        thumbnail = result.get("thumbnail", "")
        title = result.get("title", "Unknown Title")
        return f"Video downloaded successfully: {filename}", file_path, title, thumbnail, None
    except Exception as e:
        return None, None, None, None, f"Failed to download video: {e}"

def download_audio(link):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'quiet': True,
            'noplaylist': True,  # Don't download playlists
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(link, download=True)
        filename = os.listdir(DOWNLOAD_FOLDER)[-1]  # Get the last downloaded file
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        title = result.get("title", "Unknown Title")
        return f"Audio downloaded successfully: {filename}", file_path, title, None, None
    except Exception as e:
        return None, None, None, None, f"Failed to download audio: {e}"

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/start_download', methods=['POST'])
def start_download():
    data = request.get_json()
    link = data.get('url')
    choice = data.get('choice')

    if not link or not choice:
        return jsonify({'success': False, 'error': "Invalid input. Please try again."})

    if choice == 'video':
        message, file_path, title, thumbnail, error = download_video(link)
    elif choice == 'audio':
        message, file_path, title, thumbnail, error = download_audio(link)
    else:
        message, file_path, title, thumbnail, error = None, None, None, None, "Invalid choice!"

    if file_path:
        download_link = f"/download/{os.path.basename(file_path)}"
        return jsonify({
            'success': True,
            'message': message,
            'download_link': download_link,
            'title': title,
            'thumbnail': thumbnail if choice == 'video' else None,
            'choice': choice
        })
    else:
        return jsonify({'success': False, 'error': error})

@app.route('/download/<filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
