# 📦 ffmpeg-vp9-prober (Simple Usage)

A minimal guide to run the VP9 codec probing API.

---

## 🔧 Steps

1. **Clone the repository**
```bash
git clone https://github.com/ivansojivarghese/ffmpeg-vp9-prober.git
cd ffmpeg-vp9-prober
```

2. **Start a virtual environment and install required packages**
```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt  # Make sure yt-dlp is included
```

3. **Store your YouTube cookies**
- Inside the `api/` folder, place your exported **NETSCAPE format** cookies file.
- Ensure it's from your **signed-in YouTube account**.
- Name the file exactly: `cookies.txt`

4. **Send a request to the API**
```bash
curl -X POST https://ffmpeg-theta.vercel.app/api/index \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://www.youtube.com/watch?v=VISDGlpX0WI\"}"
```

📌 Replace the `url` value with the YouTube URL of any specific video.

---

## 🔄 What You Get

A JSON response containing **unique VP9 codec strings** for the available resolution streams of the video.

Example:
```json
{
  "ffprobe": [
    {
      "format_id": "248",
      "vp9_codec": "vp09.00.10.08",
      ...
    },
    ...
  ]
}
```
