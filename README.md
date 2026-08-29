# Video Uniqueizer

Fast, visually lossless tool for automating video uniqueization for Instagram Reels. Bypasses duplicate-detection algorithms by altering video and audio fingerprints while keeping pristine picture quality intact.

## Key Features
- **Micro-Zoom (100–104%):** Shifts the pixel grid without blurring or cropping out important content.
- **Micro-Speed (98–102%):** Alters video duration and audio waveform while preserving original audio pitch.
- **Micro-Color Grading:** Subtle brightness, contrast, and saturation shifts (±1.5%) that keep skin tones natural.
- **Metadata Stripping:** Wipes all camera EXIF data, creation timestamps, and encoding tags (`-map_metadata -1`).
- **Blurred Background:** Automatically pads horizontal videos into 9:16 vertical format (1080x1920).
- **GPU Accelerated:** Uses hardware NVIDIA NVENC (`h264_nvenc`) — renders a 30s 60fps video in ~3-4 seconds. Falls back to CPU (`libx264`) if no NVIDIA GPU is detected.

## Modes

### 1. Multi-Account Batch Mode (`RUN_BATCH_X12.bat`)
Generates 72 distinct unique videos and organizes them directly into separate folders for 12 Instagram Reels accounts (6 unique videos per account):
```text
output/
  ├── account_01/  ->  6 unique videos
  ├── account_02/  ->  6 unique videos
  ...
  └── account_12/  ->  6 unique videos
```
Every single file across all 12 accounts receives its own random seed and parameters, ensuring zero duplicate collision between accounts.

### 2. GUI Mode (`scripts/run_gui.bat`)
A clean PyQt5 interface for custom one-off processing with manual controls over filters, zoom ranges, speed ranges, and copy counts.

## Quick Start
1. Drop your source video(s) into `input/`.
2. Run `RUN_BATCH_X12.bat` (for batch rendering) or `scripts/run_gui.bat` (for GUI).
3. Grab the generated videos from `output/`.

## Requirements
- Windows 10/11
- Python 3.10+ (`pip install -r requirements.txt`)
- FFmpeg installed and available in system PATH
- (Optional) NVIDIA GPU for fast NVENC hardware encoding
