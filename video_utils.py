import os
import uuid
import ffmpeg
import requests
from typing import List, Optional

# Directory paths - automatically detect Modal environment vs local development
# In Modal containers: /root/uploads, /root/stitched
# In local development: uploads/, stitched/
UPLOAD_DIR = "/root/uploads" if os.path.exists("/root") else "uploads"
STITCHED_DIR = "/root/stitched" if os.path.exists("/root") else "stitched"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STITCHED_DIR, exist_ok=True)

def download_video_from_url(url: str, identifier: str, custom_upload_dir: Optional[str] = None) -> str:
    """Download video or audio from URL and save to disk with unique name"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Get file extension from URL
        file_extension = None
        try:
            # Extract filename from URL (before query parameters)
            url_path = url.split("?")[0]  # Remove query parameters
            filename = url_path.split("/")[-1]  # Get the last part of the path
            if "." in filename:
                file_extension = filename.split(".")[-1].lower()
        except:
            pass
        
        # If no extension found or it's not recognized, determine based on identifier
        if not file_extension or file_extension not in ["mp4", "avi", "mov", "mkv", "webm", "flv", "wmv", "mp3", "wav", "aac", "ogg", "m4a", "voice"]:
            if identifier == "voice":
                # For voice files, preserve the original extension or default to mp3
                file_extension = file_extension if file_extension else "mp3"
            else:
                # For videos, default to mp4
                file_extension = "mp4"
        
        # Generate a shorter, unique filename
        short_uuid = uuid.uuid4().hex[:8]  # Use only first 8 characters
        filename = f"{identifier}_{short_uuid}.{file_extension}"
        
        # Use custom directory if provided, otherwise use default
        upload_dir = custom_upload_dir if custom_upload_dir else UPLOAD_DIR
        path = os.path.join(upload_dir, filename)
        
        with open(path, "wb") as buffer:
            for chunk in response.iter_content(chunk_size=8192):
                buffer.write(chunk)
        
        return path
    except Exception as e:
        raise Exception(f"Failed to download file from {url}: {str(e)}")

def get_video_properties(video_path: str) -> dict:
    """Get video properties using ffprobe"""
    probe = ffmpeg.probe(video_path)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
    
    if not video_stream:
        raise Exception(f"No video stream found in {video_path}")
    
    return {
        'width': int(video_stream['width']),
        'height': int(video_stream['height']),
        'fps': eval(video_stream['avg_frame_rate']),
        'duration': float(video_stream['duration']),
        'has_audio': audio_stream is not None
    }

def get_audio_properties(audio_path: str) -> dict:
    """Get audio properties using ffprobe"""
    probe = ffmpeg.probe(audio_path)
    audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
    
    if not audio_stream:
        raise Exception("No audio stream found in the provided audio file")
    
    return {
        'duration': float(audio_stream['duration']),
        'sample_rate': int(audio_stream['sample_rate'])
    }

def process_video_for_concatenation(video_path: str, target_props: dict, mode: str, remove_audio: bool = False, custom_upload_dir: Optional[str] = None) -> str:
    """Process a single video to match target specifications"""
    short_uuid = uuid.uuid4().hex[:8]
    upload_dir = custom_upload_dir if custom_upload_dir else UPLOAD_DIR
    processed_path = os.path.join(upload_dir, f"processed_{short_uuid}.mp4")
    
    # Check if video has audio
    video_props = get_video_properties(video_path)
    has_audio = video_props['has_audio']
    
    print(f"Processing {os.path.basename(video_path)}: has_audio={has_audio}, remove_audio={remove_audio}")
    
    input_stream = ffmpeg.input(video_path)
    video = input_stream.video
    
    # Scale video based on mode
    if mode == "portrait":
        # For portrait mode, maintain aspect ratio and fit within target dimensions
        video = video.filter('scale', target_props['width'], target_props['height'], force_original_aspect_ratio='decrease')
        # Add padding if necessary
        video = video.filter('pad', target_props['width'], target_props['height'], '(ow-iw)/2', '(oh-ih)/2')
    else:
        # For landscape mode, scale to fit
        video = video.filter('scale', target_props['width'], target_props['height'])
    
    # Set frame rate to target
    video = video.filter('fps', fps=target_props['fps'], round='up')
    
    # Output processed file
    if not remove_audio and has_audio:
        # Keep audio - pass both video and audio streams
        audio = input_stream.audio
        ffmpeg.output(
            video,
            audio,
            processed_path,
            vcodec='libx264',
            acodec='aac',
            preset='fast',
            crf=23,
            movflags='faststart'
        ).overwrite_output().run()
    else:
        # Remove audio
        ffmpeg.output(
            video,
            processed_path,
            vcodec='libx264',
            preset='fast',
            crf=23,
            movflags='faststart',
            an=None
        ).overwrite_output().run()
    
    return processed_path

def concatenate_videos_with_voice(video_paths: List[str], voice_path: Optional[str], voice_volume: float, mode: str, custom_upload_dir: Optional[str] = None, custom_stitched_dir: Optional[str] = None, bgm_path: Optional[str] = None) -> str:
    """Concatenate multiple videos with optional voice overlay"""
    if not video_paths:
        raise ValueError("No video paths provided")
    
    # Use custom directories if provided, otherwise use defaults
    upload_dir = custom_upload_dir if custom_upload_dir else UPLOAD_DIR
    stitched_dir = custom_stitched_dir if custom_stitched_dir else STITCHED_DIR
    
    # Get properties of first video as target
    target_props = get_video_properties(video_paths[0])
    
    # Only remove audio if voice is provided
    remove_audio = voice_path is not None
    processed_paths = []
    for path in video_paths:
        processed_path = process_video_for_concatenation(path, target_props, mode, remove_audio, upload_dir)
        processed_paths.append(processed_path)
    
    # Create input file for video concatenation
    short_uuid = uuid.uuid4().hex[:8]
    txt_file_path = os.path.join(upload_dir, f"inputs_{short_uuid}.txt")
    with open(txt_file_path, "w") as f:
        for path in processed_paths:
            f.write(f"file '{os.path.abspath(path)}'\n")
    
    # Output file
    short_uuid = uuid.uuid4().hex[:8]
    output_filename = f"stitched_{short_uuid}.mp4"
    output_path = os.path.join(stitched_dir, output_filename)
    
    try:
        if voice_path or bgm_path:
            # 1. Concatenate videos with their original audio
            temp_concat_path = os.path.join(upload_dir, f"temp_concat_{uuid.uuid4().hex[:8]}.mp4")
            (
                ffmpeg
                .input(txt_file_path, format='concat', safe=0)
                .output(
                    temp_concat_path,
                    vcodec='libx264',
                    acodec='aac',
                    preset='fast',
                    crf=23,
                    movflags='faststart'
                )
                .overwrite_output()
                .run()
            )

            # 2. Process additional audio (voice and/or BGM)
            total_duration = sum(get_video_properties(path)['duration'] for path in video_paths)
            audio_inputs = []
            
            # Add original video audio as the base (only if it actually exists)
            try:
                # Actually probe the file to see if it has audio
                probe_result = ffmpeg.probe(temp_concat_path)
                has_audio_stream = any(stream['codec_type'] == 'audio' for stream in probe_result['streams'])
                
                if has_audio_stream:
                    video_audio = ffmpeg.input(temp_concat_path).audio
                    audio_inputs.append(video_audio)
                    print(f"✅ Original video audio preserved")
                else:
                    print("ℹ️  Video has no audio stream, proceeding without original audio")
            except Exception as e:
                # If probing fails, assume no audio
                print(f"ℹ️  Could not detect video audio, proceeding without original audio: {e}")
                pass
            
            print(f"🔍 Audio inputs count after video: {len(audio_inputs)}")
            
            # Process voice if provided
            if voice_path:
                voice_props = get_audio_properties(voice_path)
                voice_input = ffmpeg.input(voice_path)
                # No looping - just trim if voice is longer than video, or use as-is if shorter
                if voice_props['duration'] > total_duration:
                    voice_audio = voice_input.audio.filter('atrim', duration=total_duration)
                else:
                    voice_audio = voice_input.audio  # Use voice as-is (no padding/looping)
                voice_audio = voice_audio.filter('volume', voice_volume)
                audio_inputs.append(voice_audio)
                print(f"✅ Voice audio processed: {os.path.basename(voice_path)} (duration: {voice_props['duration']:.1f}s)")
                print(f"🔍 Audio inputs count after voice: {len(audio_inputs)}")
            
            # Process BGM if provided
            if bgm_path:
                bgm_props = get_audio_properties(bgm_path)
                bgm_input = ffmpeg.input(bgm_path)
                # BGM is already processed to match duration, just ensure it's the right length
                bgm_audio = bgm_input.audio.filter('atrim', duration=total_duration)
                audio_inputs.append(bgm_audio)
                print(f"✅ BGM audio processed: {os.path.basename(bgm_path)}")
            
            # 3. Mix all audio streams (original video audio + voice + BGM)
            if len(audio_inputs) == 0:
                # No audio streams to mix
                raise Exception("No audio streams available for mixing")
            elif len(audio_inputs) == 1:
                final_audio = audio_inputs[0]
                print(f"✅ Using single audio stream")
            else:
                # Mix all audio streams together
                final_audio = audio_inputs[0]
                for i in range(1, len(audio_inputs)):
                    final_audio = ffmpeg.filter([final_audio, audio_inputs[i]], 'amix', inputs=len(audio_inputs), duration='first')
                print(f"✅ Mixed {len(audio_inputs)} audio streams (original + voice + BGM)")
            
            # 4. Combine video and mixed audio
            video_input = ffmpeg.input(temp_concat_path)
            (
                ffmpeg
                .output(
                    video_input.video,
                    final_audio,
                    output_path,
                    vcodec='libx264',
                    acodec='aac',
                    preset='fast',
                    crf=23,
                    movflags='faststart',
                    shortest=None
                )
                .global_args('-map', '0:v')
                .global_args('-map', '1:a')
                .overwrite_output()
                .run()
            )

            # Cleanup
            if os.path.exists(temp_concat_path):
                os.unlink(temp_concat_path)
        else:
            # Concatenate videos with their original audio
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
        raise Exception(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}") from e
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