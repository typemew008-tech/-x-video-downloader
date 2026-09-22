from flask import Flask, render_template, request, jsonify, send_file
import subprocess
import tempfile
import os
import re
from pathlib import Path

app = Flask(__name__)

X_STATUS_RE = re.compile(r"https?://(?:www\.)?(?:x\.com|twitter\.com)/[^/]+/status/\d+", re.I)

def valid_url(url: str) -> bool:
    return bool(X_STATUS_RE.fullmatch(url.strip()))

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/api/info")
def info():
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", "")).strip()

    if not valid_url(url):
        return jsonify({"error": "请输入有效的 X 帖子链接"}), 400

    with tempfile.TemporaryDirectory() as tmp:
        cmd = [
            "yt-dlp",
            "--no-playlist",
            "--dump-single-json",
            "--skip-download",
            "--no-warnings",
            url,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        except subprocess.TimeoutExpired:
            return jsonify({"error": "解析超时，请稍后重试"}), 504

        if result.returncode != 0:
            msg = (result.stderr or "无法解析该帖子").strip().splitlines()[-1]
            return jsonify({"error": msg}), 422

        import json
        try:
            meta = json.loads(result.stdout)
        except json.JSONDecodeError:
            return jsonify({"error": "解析器返回了无法识别的数据"}), 502

        formats = []
        for f in meta.get("formats") or []:
            if f.get("vcodec") != "none" and f.get("url"):
                formats.append({
                    "format_id": f.get("format_id"),
                    "ext": f.get("ext"),
                    "height": f.get("height"),
                    "width": f.get("width"),
                    "fps": f.get("fps"),
                    "filesize": f.get("filesize") or f.get("filesize_approx"),
                    "url": f.get("url"),
                })

        if not formats:
            return jsonify({"error": "这个帖子没有找到公开视频，或视频暂时无法访问"}), 404

        formats.sort(key=lambda x: (x["height"] or 0, x["width"] or 0), reverse=True)
        best = formats[0]

        return jsonify({
            "title": meta.get("title") or "X 视频",
            "thumbnail": meta.get("thumbnail"),
            "duration": meta.get("duration"),
            "uploader": meta.get("uploader") or meta.get("channel"),
            "formats": formats[:8],
            "best": best,
        })

@app.post("/api/download")
def download():
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", "")).strip()

    if not valid_url(url):
        return jsonify({"error": "请输入有效的 X 帖子链接"}), 400

    tmp = tempfile.mkdtemp(prefix="xvideo-")
    output = os.path.join(tmp, "%(uploader)s-%(id)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--restrict-filenames",
        "-f", "bv*+ba/b",
        "--merge-output-format", "mp4",
        "-o", output,
        url,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return jsonify({"error": "下载超时，请重试"}), 504

    if result.returncode != 0:
        msg = (result.stderr or "下载失败").strip().splitlines()[-1]
        return jsonify({"error": msg}), 422

    candidates = list(Path(tmp).glob("*"))
    candidates = [p for p in candidates if p.is_file()]
    if not candidates:
        return jsonify({"error": "没有生成视频文件"}), 500

    path = candidates[0]
    return send_file(path, as_attachment=True, download_name=path.name, mimetype="video/mp4")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
