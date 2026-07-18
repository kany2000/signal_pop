#!/usr/bin/env python3
"""
Verify Remotion output video is not all-black before delivering.
Usage: python verify-remotion-output.py <video_path>
Exit codes: 0 = OK, 1 = all black, 2 = error
"""
import sys
import subprocess
import numpy as np
from PIL import Image

def check_video(video_path: str, sample_frames: int = 5) -> tuple[bool, str]:
    """Check if video has visible content (not all black)."""
    try:
        # Get duration
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1", video_path],
            capture_output=True, text=True, check=True
        )
        duration = float(result.stdout.strip())
        if duration <= 0:
            return False, "Invalid duration"
        
        # Sample frames at evenly distributed timestamps
        timestamps = [duration * (i + 1) / (sample_frames + 1) for i in range(sample_frames)]
        black_count = 0
        
        for ts in timestamps:
            # Extract frame
            frame_path = f"/tmp/verify_frame_{ts:.2f}.png"
            subprocess.run([
                "ffmpeg", "-v", "error", "-ss", str(ts), "-i", video_path,
                "-vf", "select='eq(n,0)',format=rgb24", "-frames:v", "1", frame_path
            ], check=True, capture_output=True)
            
            # Check if frame is all black
            img = Image.open(frame_path)
            arr = np.array(img)
            mean_val = arr.mean()
            if mean_val < 1.0:  # Essentially black
                black_count += 1
        
        if black_count == sample_frames:
            return False, f"All {sample_frames} sampled frames are black (mean < 1.0)"
        elif black_count > 0:
            return True, f"Warning: {black_count}/{sample_frames} frames appear black (fade-in/out?)"
        return True, f"OK: {sample_frames} frames have content"
        
    except subprocess.CalledProcessError as e:
        return False, f"ffmpeg/ffprobe error: {e.stderr.decode() if e.stderr else str(e)}"
    except Exception as e:
        return False, f"Error: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify-remotion-output.py <video_path>")
        sys.exit(2)
    
    ok, msg = check_video(sys.argv[1])
    print(msg)
    sys.exit(0 if ok else 1)