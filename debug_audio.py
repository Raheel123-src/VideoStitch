#!/usr/bin/env python3
"""
Debug script to test audio detection in videos
"""

import ffmpeg
import os

def check_video_audio(video_path: str):
    """Check if a video has audio and print details"""
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
        
        print(f"Video: {os.path.basename(video_path)}")
        print(f"  Has video: {video_stream is not None}")
        print(f"  Has audio: {audio_stream is not None}")
        if audio_stream:
            print(f"  Audio codec: {audio_stream.get('codec_name', 'unknown')}")
            print(f"  Audio duration: {audio_stream.get('duration', 'unknown')}")
        print()
        
        return audio_stream is not None
    except Exception as e:
        print(f"Error checking {video_path}: {e}")
        return False

def test_audio_detection():
    """Test audio detection on sample videos"""
    print("🔍 Testing Audio Detection")
    print("=" * 40)
    
    # Test with a known video that has audio
    test_video = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    
    # Download the test video
    import requests
    import uuid
    
    try:
        response = requests.get(test_video, stream=True)
        response.raise_for_status()
        
        test_path = f"test_video_{uuid.uuid4().hex[:8]}.mp4"
        with open(test_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded test video: {test_path}")
        has_audio = check_video_audio(test_path)
        
        # Clean up
        if os.path.exists(test_path):
            os.unlink(test_path)
            
        return has_audio
        
    except Exception as e:
        print(f"Error downloading test video: {e}")
        return False

if __name__ == "__main__":
    test_audio_detection() 