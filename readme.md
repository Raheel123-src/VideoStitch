# 🎞️ Video Stitcher API - Complete Documentation

A **FastAPI-based video stitching service** that combines multiple videos with optional voice overlay, background music (BGM), and persistent session management using Firebase. Deployable on Modal with S3 integration.

---

## 🚀 **API Endpoints Overview**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stitch` | POST | Start video processing (returns session ID) |
| `/status/{session_id}` | GET | Check processing status |
| `/sessions` | GET | List all sessions |
| `/delete/{session_id}` | DELETE | Delete a session |
| `/cleanup` | POST | Clean up old sessions |
| `/bgm` | GET | List available BGM options |
| `/stats` | GET | Get session statistics |
| `/health` | GET | Health check |
| `/docs` | GET | Interactive API documentation |

---

## 📋 **POST /stitch - Video Stitching Endpoint**

### **Description**
Stitch multiple videos with optional voice overlay, background music, and custom settings. Returns a session ID for tracking progress.

### **Request Body Schema**

```json
{
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
  "mode": "portrait",
  "bgm_enabled": false,
  "bgm_category": "cinematic-happy",
  "bgm_volume": 0.3
}
```

### **Field Details**

#### **Required Fields**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `videos` | Array | List of video objects to stitch | `[{"url": "...", "sequence": 1}]` |

#### **Video Object Fields**

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `url` | String | ✅ | Direct download URL for video | Must be accessible HTTP/HTTPS URL |
| `sequence` | Integer | ✅ | Stitching order (0-based) | Any integer (0, 1, 2, 3...) |

#### **Optional Fields**

| Field | Type | Default | Description | Constraints |
|-------|------|---------|-------------|-------------|
| `voice_url` | String | `null` | URL for voice/audio overlay | Any audio format (mp3, wav, aac, .voice, etc.) |
| `voice_volume` | Float | `1.0` | Voice volume multiplier | `0.0` to `2.0` |
| `mode` | String | `"portrait"` | Video orientation | `"portrait"` or `"landscape"` |
| `bgm_enabled` | Boolean | `false` | Enable background music | `true` or `false` |
| `bgm_category` | String | `null` | BGM category filter | See BGM categories below |
| `bgm_volume` | Float | `0.3` | BGM volume multiplier | `0.0` to `2.0` |

### **Response Format**

```json
{
  "session_id": "uuid-here",
  "message": "Video processing started. Use GET /status/{session_id} to check progress.",
  "status_endpoint": "/status/{session_id}"
}
```

---

## 🎵 **Background Music (BGM) System**

### **BGM Categories Available**

| Category | Description | Files |
|----------|-------------|-------|
| `cinematic-happy` | Upbeat cinematic tracks | 5 files |
| `real-estate` | Professional real estate music | 1 file |
| `for-video` | Technical/presentation music | 3 files |
| `abstract-inspire-corporate` | Corporate inspiration music | 1 file |
| `airport` | Airport/transportation music | 3 files |
| `the-background` | General background music | 1 file |

### **BGM Behavior**

- **Random Selection**: BGM is randomly selected from the specified category
- **Duration Matching**: BGM is automatically trimmed/looped to match video duration
- **Volume Control**: BGM volume can be adjusted independently of voice
- **Audio Mixing**: BGM is mixed with original video audio and voice (if provided)

### **BGM Examples**

```json
// Enable BGM with default settings
{
  "videos": [...],
  "bgm_enabled": true
}

// Custom BGM category and volume
{
  "videos": [...],
  "bgm_enabled": true,
  "bgm_category": "real-estate",
  "bgm_volume": 0.5
}
```

---

## 📊 **GET /status/{session_id} - Status Check**

### **Description**
Check the processing status of a video stitching session.

### **Response Format**

```json
{
  "session_id": "uuid-here",
  "status": "processing",
  "progress": 75,
  "message": "Uploading to S3...",
  "videos": [...],
  "voice_url": "...",
  "bgm_enabled": true,
  "bgm_category": "cinematic-happy",
  "bgm_volume": 0.3,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "s3_url": "https://s3.amazonaws.com/...",
  "error": null
}
```

### **Status Values**

| Status | Description |
|--------|-------------|
| `processing` | Video is being processed |
| `completed` | Processing finished successfully |
| `failed` | Processing failed with error |

### **Progress Values**

| Progress | Description |
|----------|-------------|
| `0-10` | Session created, starting |
| `10-40` | Downloading videos |
| `40-45` | Downloading voice file |
| `45-50` | Processing BGM |
| `50-80` | Processing and stitching videos |
| `80-100` | Uploading to S3 |
| `100` | Completed |

---

## 🔥 **Firebase Session Management**

### **Features**
- **Persistent Storage**: Sessions survive container restarts
- **Real-time Updates**: Live progress tracking across containers
- **Concurrent Processing**: Handle multiple requests simultaneously
- **Session Isolation**: Each request runs in isolated directories

### **Session Lifecycle**
1. **Creation**: Session created with initial status
2. **Processing**: Real-time progress updates
3. **Completion**: Final S3 URL returned
4. **Cleanup**: Automatic cleanup after 7 days

---

## 🚀 **Modal Deployment**

### **Prerequisites**
1. **Modal Account**: Sign up at [modal.com](https://modal.com)
2. **Firebase Project**: Create project and enable Firestore
3. **AWS S3**: Create bucket and IAM user
4. **Service Account Key**: Download Firebase service account JSON

### **Setup Commands**

```bash
# 1. Install Modal CLI
pip install modal

# 2. Login to Modal
modal token new

# 3. Create S3 credentials secret
modal secret create s3-credentials \
  AWS_ACCESS_KEY_ID=your_access_key \
  AWS_SECRET_ACCESS_KEY=your_secret_key \
  S3_BUCKET_NAME=your_bucket_name \
  AWS_DEFAULT_REGION=your_region

# 4. Create Firebase config secret
modal secret create firebase-config \
  FIREBASE_PROJECT_ID=your_project_id \
  GOOGLE_APPLICATION_CREDENTIALS=/root/serviceAccountKey.json

# 5. Deploy to Modal
modal deploy modal_app.py
```

---

## 📝 **Complete Usage Examples**

### **Basic Video Stitching**
```json
{
  "videos": [
    {"url": "https://example.com/intro.mp4", "sequence": 0},
    {"url": "https://example.com/middle.mp4", "sequence": 1},
    {"url": "https://example.com/ending.mp4", "sequence": 2}
  ]
}
```

### **Video + Voice + BGM**
```json
{
  "videos": [
    {"url": "https://example.com/video1.mp4", "sequence": 0},
    {"url": "https://example.com/video2.mp4", "sequence": 1}
  ],
  "voice_url": "https://example.com/narration.voice",
  "voice_volume": 1.2,
  "mode": "landscape",
  "bgm_enabled": true,
  "bgm_category": "cinematic-happy",
  "bgm_volume": 0.4
}
```

### **Custom Sequence Order**
```json
{
  "videos": [
    {"url": "https://example.com/intro.mp4", "sequence": 0},
    {"url": "https://example.com/ending.mp4", "sequence": 2},
    {"url": "https://example.com/middle.mp4", "sequence": 1}
  ],
  "mode": "portrait"
}
```

---

## 🔧 **Technical Details**

### **Video Processing**
- **Format Support**: MP4, AVI, MOV, MKV, WebM, FLV, WMV
- **Codec**: H.264 video, AAC audio
- **Quality**: CRF 23 (high quality)
- **Frame Rate**: Normalized to target FPS

### **Audio Processing**
- **Voice**: No looping (plays once, then silence)
- **BGM**: Automatic duration matching
- **Mixing**: Preserves original video audio
- **Volume**: Independent control for each audio stream

### **File Handling**
- **Session Isolation**: Unique directories per request
- **Automatic Cleanup**: Temporary files removed after processing
- **S3 Integration**: Final videos uploaded to S3 bucket
- **Race Condition Prevention**: Concurrent request handling

---

## 🧪 **Testing the API**

### **Local Testing**
```bash
# Start the API
uvicorn main:app --reload

# Test with curl
curl -X POST "http://localhost:8000/stitch" \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

### **Modal Testing**
```bash
# Deploy and test
modal deploy modal_app.py
curl -X POST "https://your-app.modal.run/stitch" \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

---

## 📚 **Dependencies**

### **Python Packages**
```
fastapi
uvicorn
python-multipart
ffmpeg-python
requests
boto3
python-dotenv
firebase-admin
modal
```

### **System Requirements**
- **FFmpeg**: Video processing engine
- **Python 3.12+**: Runtime environment
- **8GB RAM**: Recommended for video processing
- **8 CPU Cores**: Recommended for concurrent processing

---

## 🎯 **Key Features Summary**

✅ **Multi-video stitching** with custom sequence order  
✅ **Voice overlay** with volume control  
✅ **Background music** with category selection  
✅ **Firebase persistence** for session management  
✅ **Modal deployment** with serverless scaling  
✅ **S3 integration** for file storage  
✅ **Concurrent processing** with session isolation  
✅ **Real-time progress tracking**  
✅ **Automatic cleanup** and error handling  
✅ **Multiple video formats** support  
✅ **Portrait/Landscape** mode support  

---

## 🆘 **Support & Troubleshooting**

### **Common Issues**
1. **FFmpeg not found**: Install FFmpeg on your system
2. **Firebase connection**: Check service account key and project ID
3. **S3 upload failed**: Verify AWS credentials and bucket permissions
4. **Audio mixing errors**: Check audio file formats and durations

### **Debug Endpoints**
- `/health` - Basic health check
- `/stats` - Session statistics
- `/sessions` - List all sessions

### **Logs**
- **Local**: Check terminal output
- **Modal**: Check Modal app logs
- **Firebase**: Check Firestore database

---

**🎬 Your Video Stitcher API is ready for production use! 🚀**
