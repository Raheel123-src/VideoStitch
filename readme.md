# 🎞️ FastAPI Video Stitcher

This project is a **FastAPI-based backend service** that allows users to stitch multiple videos from URLs with optional voice overlay. It uses `ffmpeg` (via `ffmpeg-python`) to process and concatenate videos, and supports both portrait and landscape modes.

---

## 🚀 API Endpoints

### `POST /stitch`

-   **Description:** Stitch multiple videos from URLs with optional voice overlay
-   **Content-Type:** `application/json`
-   **Response:** Returns a downloadable `.mp4` video file

#### Request Body Schema:

```json
{
  "videos": [
    {
      "url": "https://storage.googleapis.com/.../video1.mp4",
      "sequence": 1
    },
    {
      "url": "https://storage.googleapis.com/.../video2.mp4", 
      "sequence": 2
    }
  ],
  "voice_url": "https://static.lisaapp.in/.../voice.mp3",
  "voice_volume": 1.0,
  "mode": "portrait"
}
```

#### Parameters:

- **videos** (required): Array of video objects
  - **url** (required): Direct download URL for the video file
  - **sequence** (required): Order number for stitching (1, 2, 3... or any order like 2, 1, 3)
- **voice_url** (optional): URL for voice/audio overlay file
- **voice_volume** (optional): Volume level for voice (0.0 to 2.0, default: 1.0)
- **mode** (optional): Video orientation ("portrait" or "landscape", default: "portrait")

#### Example using `curl`:

```bash
curl -X POST http://localhost:8000/stitch \
  -H "Content-Type: application/json" \
  -d '{
    "videos": [
      {
        "url": "https://example.com/video1.mp4",
        "sequence": 1
      },
      {
        "url": "https://example.com/video2.mp4",
        "sequence": 2
      }
    ],
    "voice_url": "https://example.com/voice.mp3",
    "voice_volume": 1.0,
    "mode": "portrait"
  }' \
  --output stitched_video.mp4
```

### `GET /health`

-   **Description:** Health check endpoint
-   **Response:** JSON status message

---

## Project Structure

.
├── main.py # FastAPI application with the /stitch endpoint
├── video_utils.py # Video handling and stitching utilities
├── uploads/ # Temporarily stores downloaded and processed videos
├── stitched/ # Stores final output videos
├── requirements.txt # List of dependencies
└── README.md # Project documentation (this file)

## 🧠 How It Works

### 1. 📥 Video Download

Videos are downloaded from the provided URLs and saved to the `uploads/` directory.

### 2. 🔢 Sequence Sorting

Videos are sorted by their sequence number to ensure correct stitching order.

### 3. 🛠️ Video Processing

Each video is processed to match the specifications:
- **Portrait Mode**: Maintains aspect ratio with padding
- **Landscape Mode**: Scales to fit target dimensions
- Frame rate normalization
- Audio removal (handled separately)

### 4. 🎵 Audio Handling

**Without voice_url:**
- Preserves original audio from each video segment
- Stitches videos with their original audio intact

**With voice_url:**
- Downloads the voice file
- Removes audio from all videos
- Loops or trims voice to match total video duration
- Applies volume adjustment
- Overlays voice on the final stitched video

### 5. ➕ Concatenation

- Videos are concatenated in sequence order
- FFmpeg handles seamless merging using the `concat` demuxer

### 6. 🧹 Cleanup

All temporary files are removed after processing:
- Downloaded videos
- Processed videos
- Voice files
- FFmpeg input lists

---

## 🧩 Dependencies

These Python libraries are required:
```
fastapi
uvicorn
python-multipart
ffmpeg-python
requests
```

Also, ensure that **FFmpeg** is installed on your system.

### ✅ Check if FFmpeg is installed

```bash
ffmpeg -version
```

### 💻 Installation Instructions by OS

#### 🖥️ macOS (via Homebrew)

```bash
brew install ffmpeg
```

#### 🖥️ Ubuntu / Debian

```bash
sudo apt update
sudo apt install ffmpeg
```

#### 🖥️ Windows

Download FFmpeg from the official site:
👉 https://ffmpeg.org/download.html

---

## 🚀 Running the API

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. Access the API:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Stitch Endpoint**: http://localhost:8000/stitch

---

## 📝 Usage Examples

### Basic Video Stitching
```json
{
  "videos": [
    {"url": "https://example.com/video1.mp4", "sequence": 1},
    {"url": "https://example.com/video2.mp4", "sequence": 2}
  ]
}
```

### With Voice Overlay
```json
{
  "videos": [
    {"url": "https://example.com/video1.mp4", "sequence": 1},
    {"url": "https://example.com/video2.mp4", "sequence": 2}
  ],
  "voice_url": "https://example.com/voice.mp3",
  "voice_volume": 1.0,
  "mode": "portrait"
}
```

### Custom Sequence Order
```json
{
  "videos": [
    {"url": "https://example.com/intro.mp4", "sequence": 1},
    {"url": "https://example.com/ending.mp4", "sequence": 3},
    {"url": "https://example.com/middle.mp4", "sequence": 2}
  ],
  "mode": "landscape"
}
```
