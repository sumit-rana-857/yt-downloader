from flask import Flask, render_template, request, send_file, redirect, url_for, session
import yt_dlp
import uuid
import os

app = Flask(__name__)
app.secret_key = "yt-secret-key"
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Progress hook
progress_info = {"status": "", "filename": "", "percent": 0}

def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0.0%').strip()
        progress_info["status"] = "downloading"
        progress_info["percent"] = percent
    elif d['status'] == 'finished':
        progress_info["status"] = "finished"
        progress_info["filename"] = d['filename']

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        session['url'] = url
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'forcejson': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                title = info.get('title', 'Video')

                clean_formats = []
                for f in formats:
                    if f.get('ext') in ['mp4', 'm4a', 'webm']:
                        label = f"{f['format_id']} - {f['ext']} - {f.get('resolution') or f.get('asr')} - {round(f.get('filesize', 0)/1024/1024, 2)} MB" if f.get('filesize') else f"{f['format_id']} - {f['ext']}"
                        clean_formats.append({'format_id': f['format_id'], 'label': label})

                return render_template("download.html", title=title, formats=clean_formats, url=url)

        except Exception as e:
            return render_template("index.html", error=f"Error: {e}")
    return render_template("index.html")


@app.route("/progress")
def progress():
    return progress_info


@app.route("/download", methods=["POST"])
def download():
    format_code = request.form.get("format")
    url = session.get("url")
    filename = str(uuid.uuid4())
    output_path = os.path.join(DOWNLOAD_FOLDER, f"{filename}.%%(ext)s")

    ydl_opts = {
        'outtmpl': output_path,
        'format': format_code,
        'progress_hooks': [progress_hook],
        'quiet': True,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            return send_file(filepath, as_attachment=True)

    except Exception as e:
        return f"Download error: {e}"
if __name__ == "__main__":
    app.run(debug=True)
