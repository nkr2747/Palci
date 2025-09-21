from flask import Flask, request, jsonify, render_template
import requests
import isodate
import re
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()
API_KEY = os.environ.get("YOUTUBE_API_KEY")


def extract_playlist_id(url):
    match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None

def get_playlist_video_ids(playlist_id):
    video_ids = []
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "contentDetails",
        "playlistId": playlist_id,
        "maxResults": 50,
        "key": API_KEY
    }
    while True:
        r = requests.get(url, params=params).json()
        for item in r.get("items", []):
            video_ids.append(item["contentDetails"]["videoId"])
        if "nextPageToken" in r:
            params["pageToken"] = r["nextPageToken"]
        else:
            break
    return video_ids

def get_videos_duration(video_ids):
    total_seconds = 0
    url = "https://www.googleapis.com/youtube/v3/videos"
    for i in range(0, len(video_ids), 50):
        ids = ",".join(video_ids[i:i+50])
        print(ids)
        params = {
            "part": "contentDetails",
            "id": ids,
            "key": API_KEY
        }
        r = requests.get(url, params=params).json()
        for item in r.get("items", []):
            duration = isodate.parse_duration(item["contentDetails"]["duration"])
            total_seconds += duration.total_seconds()
    return total_seconds

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_duration", methods=["POST"])
def get_duration():
    data = request.get_json()
    playlist_url = data.get("url")
    
    playlist_id = extract_playlist_id(playlist_url)
    
    if not playlist_id:
        return jsonify({"error": "Invalid playlist URL"}), 400
    
    ids = get_playlist_video_ids(playlist_id)
    print(ids)
    total_seconds = get_videos_duration(ids)
    return jsonify({"duration": format_time(total_seconds)})


if __name__ == "__main__":
    app.run(debug=True)
