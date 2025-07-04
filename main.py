from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import uuid

from video_utils import save_uploaded_file, concatenate_videos, cleanup_files

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/stitch")
async def stitch_videos(files: List[UploadFile] = File(...)):
    if len(files) < 1:
        raise HTTPException(status_code=400, detail="At least one file is required")
    
    saved_paths = []
    try:
        # Save uploaded files
        saved_paths = [save_uploaded_file(file, i) for i, file in enumerate(files)]
        
        # Concatenate videos
        output_path = concatenate_videos(saved_paths)
        
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