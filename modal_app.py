import modal

# Define the Modal image with essential dependencies
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install_from_requirements("requirements.txt")
    .apt_install("ffmpeg")
    # Core application files
    .add_local_file("main.py", "/root/main.py", copy=True)
    .add_local_file("video_utils.py", "/root/video_utils.py", copy=True)
    .add_local_file("s3_utils.py", "/root/s3_utils.py", copy=True)
    .add_local_file("bgm_utils.py", "/root/bgm_utils.py", copy=True)
    .add_local_file("firebase_utils.py", "/root/firebase_utils.py", copy=True)
    .add_local_file("serviceAccountKey.json", "/root/serviceAccountKey.json", copy=True)
    # BGM folder for background music
    .add_local_dir("BGM", "/root/BGM", copy=True)
    
    # Environment variables (only non-sensitive ones)
    .env({
        "UPLOAD_DIR": "/root/uploads",
        "STITCHED_DIR": "/root/stitched"
    })
    
    # Create necessary directories for video processing
    .run_commands(
        "mkdir -p /root/uploads",
        "mkdir -p /root/stitched"
    )
)

# Define the Modal App
app = modal.App("video-stitcher-api", image=image)

# Expose the FastAPI app as a web endpoint
@app.function(
    timeout=1800,  # 30 min timeout for video processing
    cpu=8,  # 8 CPU cores (sufficient for video processing)
    memory=4096,  # 4GB RAM (sufficient for most video operations)
    max_containers=20,  # Allow up to 20 containers
            secrets=[
            modal.Secret.from_name("s3-credentials"),  # All S3 config in one secret
            modal.Secret.from_name("firebase-config")  # Firebase configuration
        ],
)
@modal.concurrent(max_inputs=15)
@modal.asgi_app()
def fastapi_app():
    import sys
    import os
    
    # Add root to Python path
    if "/root" not in sys.path:
        sys.path.append("/root")
    
    # Debug: Check environment variables from Modal secrets
    print("[MODAL DEPLOYMENT] 🔍 Checking environment variables:")
    print(f"[MODAL DEPLOYMENT] AWS_ACCESS_KEY_ID: {'✅ Set' if os.environ.get('AWS_ACCESS_KEY_ID') else '❌ Missing'}")
    print(f"[MODAL DEPLOYMENT] AWS_SECRET_ACCESS_KEY: {'✅ Set' if os.environ.get('AWS_SECRET_ACCESS_KEY') else '❌ Missing'}")
    print(f"[MODAL DEPLOYMENT] S3_BUCKET_NAME: {'✅ Set' if os.environ.get('S3_BUCKET_NAME') else '❌ Missing'}")
    print(f"[MODAL DEPLOYMENT] AWS_DEFAULT_REGION: {'✅ Set' if os.environ.get('AWS_DEFAULT_REGION') else '❌ Missing'}")
    
    # Verify video processing system is available
    try:
        from video_utils import download_video_from_url, concatenate_videos_with_voice, cleanup_files
        print("[MODAL DEPLOYMENT] ✅ Video processing utilities loaded successfully")
    except Exception as e:
        print(f"[MODAL DEPLOYMENT] ⚠️  Warning: Video processing utilities not available: {e}")
    
    # Verify S3 utilities are available
    try:
        from s3_utils import upload_to_s3, get_s3_bucket_name, generate_s3_key
        print("[MODAL DEPLOYMENT] ✅ S3 utilities loaded successfully")
    except Exception as e:
        print(f"[MODAL DEPLOYMENT] ⚠️  Warning: S3 utilities not available: {e}")
    
            # Verify BGM utilities are available
        try:
            from bgm_utils import BGMSelector, process_bgm_for_video
            print("[MODAL DEPLOYMENT] ✅ BGM utilities loaded successfully")
        except Exception as e:
            print(f"[MODAL DEPLOYMENT] ⚠️  Warning: BGM utilities not available: {e}")
        
        # Verify Firebase utilities are available
        try:
            from firebase_utils import create_session, update_session_status, get_session
            print("[MODAL DEPLOYMENT] ✅ Firebase utilities loaded successfully")
        except Exception as e:
            print(f"[MODAL DEPLOYMENT] ⚠️  Warning: Firebase utilities not available: {e}")
        
        # Verify required Python modules
        try:
            import shutil
            import threading
            import concurrent.futures
            import ffmpeg
            print("[MODAL DEPLOYMENT] ✅ Required Python modules loaded successfully")
        except Exception as e:
            print(f"[MODAL DEPLOYMENT] ⚠️  Warning: Required Python modules not available: {e}")
    
    # Import and return the FastAPI app
    from main import app
    print("[MODAL DEPLOYMENT] ✅ Video Stitcher API loaded successfully")
    return app
