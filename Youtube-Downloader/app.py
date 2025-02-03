from flask import Flask, request, render_template, send_from_directory, jsonify
import yt_dlp as youtube_dl
import os
from time import sleep
import traceback
import urllib.parse
import random
import string

app = Flask(__name__, static_url_path='/static')

# Helper function to generate a unique filename from the URL
def generate_filename_from_url(url):
    parsed_url = urllib.parse.urlparse(url)
    filename_base = parsed_url.netloc + parsed_url.path.replace('/', '_')
    unique_filename = f"{filename_base}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}.mp4"
    return unique_filename

@app.route('/', methods=['POST', 'GET'])
def send():
    if request.method == 'POST':
        link = request.form['link']
        format_id = request.form['format_id']
        try:
            filename = generate_filename_from_url(link)
            download_opts = {
                'format': format_id,
                'outtmpl': f'downloads/{filename}',  
            }
            with youtube_dl.YoutubeDL(download_opts) as ydl:
                ydl.download([link])
            
            return send_from_directory('downloads', filename, as_attachment=True)
        except Exception as e:
            print(f"Error: {e}")
            return render_template('errorpage.html')
    return render_template("main.html")

@app.route('/get_formats', methods=['GET'])
def get_formats():
    link = request.args.get('link')
    if not link:
        return jsonify({'error': 'No URL provided'}), 400
    try:
        with youtube_dl.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(link, download=False)
            formats = []
            for fmt in info['formats']:
                if fmt['ext'] == 'mp4':  
                    resolution = fmt.get('resolution', None)
                    filesize = fmt.get('filesize', None)

                    if resolution not in [None, 'Unknown'] and filesize not in [None, 'Unknown']:
                        formats.append({
                            'format_id': fmt['format_id'],
                            'ext': fmt['ext'],
                            'resolution': resolution,
                            'filesize': f"{filesize / 1024 / 1024:.2f} MB" if filesize else "Unknown",
                        })
        return jsonify({'formats': formats, 'title': info['title']})
    except Exception as e:
        print("Error fetching formats:")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
