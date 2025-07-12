#!/usr/bin/env python3
"""
Test script for the Video Stitcher API
This script demonstrates how to test the new JSON-based API
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_basic_stitch():
    """Test basic video stitching without voice"""
    print("🎬 Testing basic video stitching...")
    
    # Sample request (replace with actual video URLs)
    payload = {
        "videos": [
            {
                "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
                "sequence": 1
            },
            {
                "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_2mb.mp4", 
                "sequence": 2
            }
        ],
        "mode": "portrait"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/stitch",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            # Save the video file
            with open("test_output.mp4", "wb") as f:
                f.write(response.content)
            print("✅ Video stitched successfully! Saved as 'test_output.mp4'")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    print()

def test_stitch_with_voice():
    """Test video stitching with voice overlay"""
    print("🎵 Testing video stitching with voice overlay...")
    
    # Sample request with voice (replace with actual URLs)
    payload = {
        "videos": [
            {
                "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
                "sequence": 1
            },
            {
                "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_2mb.mp4",
                "sequence": 2
            }
        ],
        "voice_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
        "voice_volume": 1.0,
        "mode": "portrait"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/stitch",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            # Save the video file
            with open("test_output_with_voice.mp4", "wb") as f:
                f.write(response.content)
            print("✅ Video stitched with voice successfully! Saved as 'test_output_with_voice.mp4'")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    print()

def test_custom_sequence():
    """Test video stitching with custom sequence order"""
    print("🔄 Testing custom sequence order...")
    
    payload = {
        "videos": [
            {
                "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
                "sequence": 2  # This will be second
            },
            {
                "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_2mb.mp4",
                "sequence": 1  # This will be first
            },
            {
                "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_5mb.mp4",
                "sequence": 3  # This will be third
            }
        ],
        "mode": "landscape"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/stitch",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            # Save the video file
            with open("test_output_custom_sequence.mp4", "wb") as f:
                f.write(response.content)
            print("✅ Video stitched with custom sequence! Saved as 'test_output_custom_sequence.mp4'")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    print()

def test_validation():
    """Test API validation"""
    print("🔍 Testing API validation...")
    
    # Test with invalid voice_volume
    payload = {
        "videos": [
            {
                "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
                "sequence": 1
            }
        ],
        "voice_volume": 3.0  # Invalid: should be 0-2
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/stitch",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    print()

if __name__ == "__main__":
    print("🚀 Video Stitcher API Test Suite")
    print("=" * 40)
    
    # Run tests
    test_health()
    test_validation()
    test_basic_stitch()
    test_stitch_with_voice()
    test_custom_sequence()
    
    print("✨ Test suite completed!")
    print("\n📝 Note: Replace the sample URLs with actual video URLs for real testing.") 