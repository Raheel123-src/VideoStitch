from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import uuid
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from video_utils import download_video_from_url, concatenate_videos_with_voice, cleanup_files
from s3_utils import upload_to_s3, get_s3_bucket_name, generate_s3_key
from bgm_utils import BGMSelector, process_bgm_for_video
from firebase_utils import create_session, update_session_status, get_session, list_sessions, delete_session, cleanup_old_sessions, get_session_stats
import ffmpeg

app = FastAPI(
    title="Video Stitcher API",
    description="Session-based video stitching API with concurrent processing",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoItem(BaseModel):
    url: str
    sequence: int

class StitchRequest(BaseModel):
    videos: List[VideoItem]
    voice_url: Optional[str] = None
    voice_volume: Optional[float] = 1.0
    mode: Optional[str] = "portrait"
    bgm_enabled: Optional[bool] = False
    bgm_category: Optional[str] = None  # e.g., "cinematic-happy", "real-estate"
    bgm_volume: Optional[float] = 0.3  # Default BGM volume (lower than voice)

class StitchResponse(BaseModel):
    success: bool
    message: str
    video_url: str
    filename: str

class StitchStatus(BaseModel):
    session_id: str
    status: str  # "processing", "completed", "failed"
    progress: int  # 0-100
    message: str
    video_url: Optional[str] = None
    filename: Optional[str] = None
    created_at: float
    updated_at: float

# Firebase session management (persistent storage)
# No need for in-memory storage or locks - Firebase handles concurrency
executor = ThreadPoolExecutor(max_workers=10)  # Handle up to 10 concurrent requests

@app.post("/stitch")
async def stitch_videos(request: StitchRequest, background_tasks: BackgroundTasks):
    """
    Stitch videos endpoint - creates a session and processes videos in background
    Returns session ID for status tracking
    """
    if len(request.videos) < 1:
        raise HTTPException(status_code=400, detail="At least one video is required")
    
    # Validate voice_volume
    if request.voice_volume is not None and (request.voice_volume < 0 or request.voice_volume > 2):
        raise HTTPException(status_code=400, detail="voice_volume must be between 0 and 2")
    
    # Validate mode
    if request.mode not in ["portrait", "landscape"]:
        raise HTTPException(status_code=400, detail="mode must be either 'portrait' or 'landscape'")
    
    # Validate BGM settings
    if request.bgm_enabled:
        if request.bgm_volume is not None and (request.bgm_volume < 0 or request.bgm_volume > 2):
            raise HTTPException(status_code=400, detail="bgm_volume must be between 0 and 2")
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    current_time = time.time()
    
    # Create session in Firebase
    create_session(
        session_id=session_id,
        videos=[video.dict() for video in request.videos],
        voice_url=request.voice_url,
        voice_volume=request.voice_volume or 1.0,
        mode=request.mode or "portrait",
        bgm_enabled=request.bgm_enabled or False,
        bgm_category=request.bgm_category,
        bgm_volume=request.bgm_volume or 0.3
    )
    
    # Start background processing
    background_tasks.add_task(
        process_videos_background,
        session_id,
        request.videos,
        request.voice_url,
        request.voice_volume or 1.0,
        request.mode or "portrait",
        request.bgm_enabled or False,
        request.bgm_category,
        request.bgm_volume or 0.3
    )
    
    return {
        "session_id": session_id,
        "message": "Video processing started. Use GET /status/{session_id} to check progress.",
        "status_endpoint": f"/status/{session_id}"
    }

def process_videos_background(session_id: str, videos: List[VideoItem], voice_url: Optional[str], voice_volume: float, mode: str, bgm_enabled: bool, bgm_category: Optional[str], bgm_volume: float):
    """
    Background function to process videos in a separate thread
    """
    # Create session-specific directories
    session_upload_dir = os.path.join("uploads", session_id)
    session_stitched_dir = os.path.join("stitched", session_id)
    
    # Ensure directories exist
    os.makedirs(session_upload_dir, exist_ok=True)
    os.makedirs(session_stitched_dir, exist_ok=True)
    
    try:
        # Update status in Firebase
        update_session_status(session_id, status="processing", progress=10, message="Downloading videos...")
        
        # Sort videos by sequence
        sorted_videos = sorted(videos, key=lambda x: x.sequence)
        
        saved_paths = []
        voice_path = None
        
        # Download videos to session-specific directory
        for i, video in enumerate(sorted_videos):
            video_path = download_video_from_url(video.url, str(video.sequence), session_upload_dir)
            saved_paths.append(video_path)
            
            # Update progress in Firebase
            progress = 10 + int((i + 1) / len(sorted_videos) * 30)
            update_session_status(session_id, status="processing", progress=progress, message=f"Downloaded {i + 1}/{len(sorted_videos)} videos...")
        
        # Download voice file if provided
        if voice_url:
            update_session_status(session_id, status="processing", progress=40, message="Downloading voice file...")
            
            try:
                voice_path = download_video_from_url(voice_url, "voice", session_upload_dir)
            except Exception as e:
                raise Exception(f"Failed to download voice file: {str(e)}")
        
        # Process BGM if enabled
        bgm_path = None
        if bgm_enabled:
            update_session_status(session_id, status="processing", progress=45, message="Selecting and processing BGM...")
            
            try:
                # Initialize BGM selector
                bgm_selector = BGMSelector()
                
                # Get random BGM (with category filter if specified)
                bgm_path = bgm_selector.get_random_bgm(bgm_category)
                
                if bgm_path:
                    # Calculate total video duration for BGM processing
                    total_duration = 0
                    for video_path in saved_paths:
                        probe = ffmpeg.probe(video_path)
                        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
                        if video_stream:
                            total_duration += float(video_stream.get('duration', 0))
                    
                    # Process BGM to match video duration and volume
                    bgm_path = process_bgm_for_video(
                        bgm_path, 
                        total_duration, 
                        bgm_volume, 
                        session_upload_dir
                    )
                    
                    print(f"✅ BGM processed: {os.path.basename(bgm_path)}")
                else:
                    print("⚠️  No BGM found, proceeding without background music")
                    
            except Exception as e:
                print(f"⚠️  BGM processing failed: {str(e)}, proceeding without BGM")
                bgm_path = None
        
        # Update status for processing
        update_session_status(session_id, status="processing", progress=50, message="Processing and stitching videos...")
        
        # Concatenate videos with session-specific output directory
        output_path = concatenate_videos_with_voice(
            saved_paths, 
            voice_path, 
            voice_volume,
            mode,
            session_upload_dir,
            session_stitched_dir,
            bgm_path
        )
        
        # Update status for S3 upload
        update_session_status(session_id, status="processing", progress=80, message="Uploading to S3...")
        
        # Upload to S3
        bucket_name = get_s3_bucket_name()
        s3_key = generate_s3_key(os.path.basename(output_path))
        video_url = upload_to_s3(output_path, bucket_name, s3_key)
        
        # Update status to completed in Firebase
        update_session_status(
            session_id, 
            status="completed", 
            progress=100, 
            message="Videos stitched successfully and uploaded to S3",
            s3_url=video_url
        )
        
    except Exception as e:
        # Update status to failed in Firebase
        update_session_status(
            session_id, 
            status="failed", 
            progress=0,  # Reset progress on failure
            message=f"Processing failed: {str(e)}",
            error=str(e)
        )
    finally:
        # Cleanup temporary files and session directories
        if 'saved_paths' in locals() and saved_paths:
            cleanup_files(saved_paths)
        if 'voice_path' in locals() and voice_path and os.path.exists(voice_path):
            os.unlink(voice_path)
        if 'bgm_path' in locals() and bgm_path and os.path.exists(bgm_path):
            os.unlink(bgm_path)
        
        # Clean up session directories after a delay (allow for file operations to complete)
        def cleanup_session_dirs():
            import time
            time.sleep(5)  # Wait 5 seconds before cleanup
            try:
                if os.path.exists(session_upload_dir):
                    import shutil
                    shutil.rmtree(session_upload_dir)
                if os.path.exists(session_stitched_dir):
                    import shutil
                    shutil.rmtree(session_stitched_dir)
            except Exception as e:
                print(f"Warning: Could not cleanup session directories for {session_id}: {e}")
        
        # Start cleanup in background
        import threading
        cleanup_thread = threading.Thread(target=cleanup_session_dirs)
        cleanup_thread.daemon = True
        cleanup_thread.start()

@app.get("/status/{session_id}")
async def get_status(session_id: str):
    """
    Get the status of a video processing session from Firebase
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session

@app.get("/sessions")
async def list_sessions():
    """
    List all sessions from Firebase
    """
    sessions_data = list_sessions(limit=100)
    return {
        "total_sessions": len(sessions_data),
        "sessions": sessions_data
    }

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session from Firebase and cleanup directories
    """
    # Check if session exists in Firebase
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Clean up session directories
    session_upload_dir = os.path.join("uploads", session_id)
    session_stitched_dir = os.path.join("stitched", session_id)
    
    try:
        if os.path.exists(session_upload_dir):
            import shutil
            shutil.rmtree(session_upload_dir)
        if os.path.exists(session_stitched_dir):
            import shutil
            shutil.rmtree(session_stitched_dir)
    except Exception as e:
        print(f"Warning: Could not cleanup session directories for {session_id}: {e}")
    
    # Delete from Firebase
    delete_session(session_id)
    return {"message": "Session deleted successfully"}

@app.post("/cleanup")
async def cleanup_completed_sessions():
    """
    Clean up old completed or failed sessions from Firebase
    """
    # Use Firebase cleanup function
    cleaned_count = cleanup_old_sessions(days_old=7)
    
    return {
        "message": f"Cleaned up {cleaned_count} old completed/failed sessions from Firebase",
        "cleaned_sessions": cleaned_count
    }

@app.get("/stats")
async def get_session_stats():
    """
    Get session statistics from Firebase
    """
    return get_session_stats()

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Video Stitcher API v3.0",
        "description": "Session-based video stitching with Firebase persistence and concurrent processing",
        "endpoints": {
            "POST /stitch": "Start video processing (returns session ID)",
            "GET /status/{session_id}": "Check processing status from Firebase",
            "GET /sessions": "List all sessions from Firebase",
            "DELETE /sessions/{session_id}": "Delete a session from Firebase",
            "POST /cleanup": "Clean up old sessions from Firebase",
            "GET /stats": "Get session statistics from Firebase",
            "GET /bgm": "List available BGM categories and files",
            "GET /health": "Health check",
            "GET /docs": "Interactive API documentation"
        },
        "features": [
            "Concurrent video processing",
            "Session-based tracking",
            "Real-time progress updates",
            "S3 integration",
            "Background processing",
            "Background music integration"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "message": "Video Stitcher API is running in S3 mode with session management"
    }

@app.get("/bgm")
async def list_bgm():
    """List available BGM categories and files"""
    try:
        bgm_selector = BGMSelector()
        categories = bgm_selector.get_bgm_categories()
        all_bgm = bgm_selector.list_all_bgm()
        
        # Group BGM files by category
        bgm_by_category = {}
        for file_path, category, filename in all_bgm:
            if category not in bgm_by_category:
                bgm_by_category[category] = []
            
            # Get file info
            try:
                info = get_bgm_info(file_path)
                bgm_by_category[category].append({
                    "filename": filename,
                    "duration": info.get('duration', 'unknown'),
                    "sample_rate": info.get('sample_rate', 'unknown'),
                    "channels": info.get('channels', 'unknown'),
                    "codec": info.get('codec', 'unknown'),
                    "file_size": info.get('file_size', 'unknown')
                })
            except Exception as e:
                bgm_by_category[category].append({
                    "filename": filename,
                    "error": str(e)
                })
        
        return {
            "total_categories": len(categories),
            "total_files": len(all_bgm),
            "categories": categories,
            "bgm_files": bgm_by_category
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list BGM: {str(e)}")