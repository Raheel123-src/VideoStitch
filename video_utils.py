import os
import uuid
import ffmpeg
from typing import List
from fastapi import UploadFile

UPLOAD_DIR = "uploads"
STITCHED_DIR = "stitched"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STITCHED_DIR, exist_ok=True)

def save_uploaded_file(file: UploadFile, index: int) -> str:
    """Save uploaded file to disk with unique name"""
    filename = f"{index}_{uuid.uuid4().hex}_{file.filename}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as buffer:
        buffer.write(file.file.read())
    return path

def get_video_properties(video_path: str) -> dict:
    """Get video properties using ffprobe"""
    probe = ffmpeg.probe(video_path)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
    
    return {
        'width': int(video_stream['width']),
        'height': int(video_stream['height']),
        'fps': eval(video_stream['avg_frame_rate']),
        'duration': float(video_stream['duration']),
        'has_audio': audio_stream is not None
    }

def concatenate_videos(video_paths: List[str]) -> str:
    """Concatenate multiple videos with re-encoding for compatibility"""
    if not video_paths:
        raise ValueError("No video paths provided")
    
    # Get properties of first video as target
    target_props = get_video_properties(video_paths[0])
    
    # Process each video to match target specs
    processed_paths = []
    for i, path in enumerate(video_paths):
        processed_path = os.path.join(UPLOAD_DIR, f"processed_{i}_{uuid.uuid4().hex}.mp4")
        
        input_stream = ffmpeg.input(path)
        video = input_stream.video
        
        # Scale video to target resolution
        video = video.filter('scale', target_props['width'], target_props['height'])
        
        # Set frame rate to target
        video = video.filter('fps', fps=target_props['fps'], round='up')
        
        # Handle audio if present
        audio = None
        if get_video_properties(path)['has_audio']:
            audio = input_stream.audio
            
        # Output processed file
        streams = [video]
        if audio:
            streams.append(audio)
            
        ffmpeg.output(
            *streams,
            processed_path,
            vcodec='libx264',
            acodec='aac',
            preset='fast',
            crf=23,
            movflags='faststart'
        ).overwrite_output().run()
        
        processed_paths.append(processed_path)
    
    # Create input file for concatenation
    txt_file_path = os.path.join(UPLOAD_DIR, f"inputs_{uuid.uuid4().hex}.txt")
    with open(txt_file_path, "w") as f:
        for path in processed_paths:
            f.write(f"file '{os.path.abspath(path)}'\n")
    
    # Output file
    output_filename = f"stitched_{uuid.uuid4().hex}.mp4"
    output_path = os.path.join(STITCHED_DIR, output_filename)
    
    # Concatenate using ffmpeg
    try:
        (
            ffmpeg
            .input(txt_file_path, format='concat', safe=0)
            .output(
                output_path,
                vcodec='libx264',
                acodec='aac',
                preset='fast',
                crf=23,
                movflags='faststart'
            )
            .overwrite_output()
            .run()
        )
    except ffmpeg.Error as e:
        raise Exception(f"FFmpeg error: {e.stderr.decode()}") from e
    finally:
        # Cleanup processed files and input list
        for path in processed_paths:
            if os.path.exists(path):
                os.unlink(path)
        if os.path.exists(txt_file_path):
            os.unlink(txt_file_path)
    
    return output_path

def cleanup_files(file_paths: List[str]):
    """Clean up temporary files"""
    for path in file_paths:
        if os.path.exists(path):
            os.unlink(path)