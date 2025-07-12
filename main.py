from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid

from video_utils import download_video_from_url, concatenate_videos_with_voice, cleanup_files

app = FastAPI()

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

@app.post("/stitch")
async def stitch_videos(request: StitchRequest):
    if len(request.videos) < 1:
        raise HTTPException(status_code=400, detail="At least one video is required")
    
    # Validate voice_volume
    if request.voice_volume is not None and (request.voice_volume < 0 or request.voice_volume > 2):
        raise HTTPException(status_code=400, detail="voice_volume must be between 0 and 2")
    
    # Validate mode
    if request.mode not in ["portrait", "landscape"]:
        raise HTTPException(status_code=400, detail="mode must be either 'portrait' or 'landscape'")
    
    # Sort videos by sequence
    sorted_videos = sorted(request.videos, key=lambda x: x.sequence)
    
    saved_paths = []
    voice_path = None
    
    try:
        # Download videos from URLs
        for video in sorted_videos:
            video_path = download_video_from_url(video.url, str(video.sequence))
            saved_paths.append(video_path)
        
        # Download voice file if provided
        if request.voice_url:
            try:
                voice_path = download_video_from_url(request.voice_url, "voice")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to download voice file: {str(e)}")
        
        # Concatenate videos with voice overlay
        output_path = concatenate_videos_with_voice(
            saved_paths, 
            voice_path, 
            request.voice_volume or 1.0,
            request.mode or "portrait"
        )
        
        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename=os.path.basename(output_path)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temporary files
        if saved_paths:
            cleanup_files(saved_paths)
        if voice_path and os.path.exists(voice_path):
            os.unlink(voice_path)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Video Stitcher API is running"}