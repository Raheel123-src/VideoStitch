# 🎞️ FastAPI Video Stitcher

This project is a **FastAPI-based backend service** that allows users to upload multiple video files and returns a single stitched `.mp4` video. It uses `ffmpeg` (via `ffmpeg-python`) to process and concatenate videos, and is **deployed live on Render**.

---

## Live API

> ✅ **Deployed on Render**  
> Access your API at:  
> `https://<your-app-name>.onrender.com`

> Replace `<your-app-name>` with your actual Render deployment name.

---

## 🚀 API Endpoint

### `POST /stitch`

-   **Description:** Upload multiple video files to get a single stitched video in return.
-   **Form Field:** `files` (List of video files as `UploadFile`)
-   **Response:** Returns a downloadable `.mp4` video file

#### Example using `curl`:

```bash
curl -X POST http://localhost:8000/stitch \
  -F "files=@video1.mp4" \
  -F "files=@video2.mp4" \
  --output output.mp4
```

## Project Structure

.
├── main.py # FastAPI application with the /stitch endpoint
├── video_utils.py # Video handling and stitching utilities
├── uploads/ # Temporarily stores uploaded and processed videos
├── stitched/ # Stores final output videos
├── requirements.txt # List of dependencies
└── README.md # Project documentation (this file)

## 🧠 How It Works

### 1. 📤 File Upload

Files are uploaded through a `multipart/form-data` `POST` request to the `/stitch` endpoint.

### 2. 💾 Saving Files

Each uploaded file is saved to the `uploads/` directory with a unique UUID-prefixed filename using `save_uploaded_file()`.

### 3. 🛠️ Video Normalization

Each video is:

-   Rescaled to match the resolution of the first video
-   Re-encoded to have the same FPS and codec (`H.264` for video, `AAC` for audio)
-   Audio is retained if available

### 4. ➕ Concatenation

-   A temporary `.txt` file lists all processed video paths
-   FFmpeg reads this file and merges the clips seamlessly using the `concat` demuxer

### 5. 🧹 Cleanup

All temporary files are removed after stitching:

-   Uploaded files
-   Intermediate processed videos
-   FFmpeg `.txt` list file

---

## 🧩 Dependencies

These Python libraries are required:
fastapi
uvicorn
python-multipart
ffmpeg-python

pgsql

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
brew install ffmpeg
```

#### 🖥️ Windows

Download FFmpeg from the official site:
👉 https://ffmpeg.org/download.html
