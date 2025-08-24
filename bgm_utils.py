import os
import random
import glob
from typing import List, Optional, Tuple
import ffmpeg

class BGMSelector:
    """Background Music Selector and Processor"""
    
    def __init__(self, bgm_root_dir: str = "BGM"):
        self.bgm_root_dir = bgm_root_dir
        self.bgm_files = self._discover_bgm_files()
    
    def _discover_bgm_files(self) -> List[Tuple[str, str, str]]:
        """
        Discover all BGM files in the BGM directory
        Returns: List of tuples (file_path, category, filename)
        """
        bgm_files = []
        
        if not os.path.exists(self.bgm_root_dir):
            print(f"Warning: BGM directory '{self.bgm_root_dir}' not found")
            return bgm_files
        
        # Walk through all subdirectories
        for root, dirs, files in os.walk(self.bgm_root_dir):
            for file in files:
                # Check if it's an audio file
                if file.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg')):
                    # Extract category from folder name
                    category = os.path.basename(root)
                    file_path = os.path.join(root, file)
                    bgm_files.append((file_path, category, file))
        
        print(f"Discovered {len(bgm_files)} BGM files in {len(set(f[1] for f in bgm_files))} categories")
        return bgm_files
    
    def get_random_bgm(self, category: Optional[str] = None) -> Optional[str]:
        """
        Get a random BGM file
        Args:
            category: Optional category filter (e.g., 'cinematic-happy', 'real-estate')
        Returns:
            Path to random BGM file or None if no files found
        """
        if not self.bgm_files:
            print("No BGM files found")
            return None
        
        if category:
            # Filter by category
            print(f"🔍 Looking for BGM in category: '{category}'")
            print(f"📁 Available categories: {[f[1] for f in self.bgm_files]}")
            category_files = [f for f in self.bgm_files if category.lower() in f[1].lower()]
            print(f"🎵 Found {len(category_files)} files in category '{category}'")
            if not category_files:
                print(f"❌ No BGM files found in category: {category}")
                return None
            selected = random.choice(category_files)
        else:
            # Random selection from all files
            selected = random.choice(self.bgm_files)
        
        print(f"✅ Selected BGM: {selected[2]} from category: {selected[1]}")
        return selected[0]
    
    def get_bgm_categories(self) -> List[str]:
        """Get list of available BGM categories"""
        return list(set(f[1] for f in self.bgm_files))
    
    def get_bgm_by_category(self, category: str) -> List[str]:
        """Get all BGM files in a specific category"""
        return [f[0] for f in self.bgm_files if category.lower() in f[1].lower()]
    
    def list_all_bgm(self) -> List[Tuple[str, str, str]]:
        """List all available BGM files with their categories"""
        return self.bgm_files.copy()

def process_bgm_for_video(bgm_path: str, video_duration: float, bgm_volume: float = 1.0, output_dir: str = "uploads") -> str:
    """
    Process BGM to match video duration and volume
    Args:
        bgm_path: Path to BGM file
        video_duration: Duration of the video in seconds
        bgm_volume: Volume multiplier (0.0 to 2.0)
        output_dir: Directory to save processed BGM
    Returns:
        Path to processed BGM file
    """
    import uuid
    
    # Generate unique filename
    bgm_filename = f"processed_bgm_{uuid.uuid4().hex[:8]}.aac"
    output_path = os.path.join(output_dir, bgm_filename)
    
    try:
        # Get BGM properties
        probe = ffmpeg.probe(bgm_path)
        bgm_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
        
        if not bgm_stream:
            raise Exception("No audio stream found in BGM file")
        
        bgm_duration = float(bgm_stream.get('duration', 0))
        
        print(f"Processing BGM: {os.path.basename(bgm_path)}")
        print(f"BGM duration: {bgm_duration:.2f}s, Video duration: {video_duration:.2f}s")
        print(f"BGM volume: {bgm_volume}")
        
        # Create input stream
        input_stream = ffmpeg.input(bgm_path)
        audio = input_stream.audio
        
        # Apply volume
        if bgm_volume != 1.0:
            audio = audio.filter('volume', bgm_volume)
        
        # Handle duration matching
        if bgm_duration < video_duration:
            # Loop BGM to fill video duration
            print(f"Looping BGM to fill {video_duration:.2f}s")
            audio = audio.filter('aloop', loop=-1, size=int(video_duration * int(bgm_stream.get('sample_rate', 44100))))
            audio = audio.filter('atrim', duration=video_duration)
        else:
            # Trim BGM to video duration
            print(f"Trimming BGM to {video_duration:.2f}s")
            audio = audio.filter('atrim', duration=video_duration)
        
        # Output processed BGM
        ffmpeg.output(
            audio,
            output_path,
            acodec='aac',
            ar=44100,  # Sample rate
            ac=2,      # Audio channels (stereo)
            ab='128k'  # Bitrate
        ).overwrite_output().run()
        
        print(f"✅ BGM processed successfully: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Error processing BGM: {str(e)}")
        raise Exception(f"Failed to process BGM: {str(e)}")

def get_bgm_info(bgm_path: str) -> dict:
    """
    Get information about a BGM file
    Args:
        bgm_path: Path to BGM file
    Returns:
        Dictionary with BGM information
    """
    try:
        probe = ffmpeg.probe(bgm_path)
        audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
        
        if not audio_stream:
            return {"error": "No audio stream found"}
        
        return {
            "filename": os.path.basename(bgm_path),
            "duration": float(audio_stream.get('duration', 0)),
            "sample_rate": int(audio_stream.get('sample_rate', 0)),
            "channels": int(audio_stream.get('channels', 0)),
            "codec": audio_stream.get('codec_name', 'unknown'),
            "bitrate": audio_stream.get('bit_rate', 'unknown'),
            "file_size": os.path.getsize(bgm_path) if os.path.exists(bgm_path) else 'unknown'
        }
    except Exception as e:
        return {"error": str(e)}

# Example usage and testing
if __name__ == "__main__":
    print("🎵 BGM Utility Test")
    print("=" * 30)
    
    # Initialize BGM selector
    bgm_selector = BGMSelector()
    
    # List all categories
    categories = bgm_selector.get_bgm_categories()
    print(f"\n📁 Available BGM categories: {len(categories)}")
    for category in categories:
        print(f"  - {category}")
    
    # List all BGM files
    all_bgm = bgm_selector.list_all_bgm()
    print(f"\n🎵 Total BGM files: {len(all_bgm)}")
    for file_path, category, filename in all_bgm[:5]:  # Show first 5
        print(f"  - {filename} ({category})")
    
    if len(all_bgm) > 5:
        print(f"  ... and {len(all_bgm) - 5} more files")
    
    # Test random selection
    print(f"\n🎲 Random BGM selection:")
    for i in range(3):
        random_bgm = bgm_selector.get_random_bgm()
        if random_bgm:
            info = get_bgm_info(random_bgm)
            print(f"  {i+1}. {os.path.basename(random_bgm)} - {info.get('duration', 'unknown'):.1f}s")
    
    # Test category-specific selection
    if categories:
        test_category = categories[0]
        print(f"\n🎯 BGM from category '{test_category}':")
        category_bgm = bgm_selector.get_bgm_by_category(test_category)
        for bgm in category_bgm[:3]:  # Show first 3
            print(f"  - {os.path.basename(bgm)}")
