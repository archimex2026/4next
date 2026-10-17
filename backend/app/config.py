import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
MEDIA_DIR = BASE_DIR / "media"
DB_PATH = BASE_DIR / "book2course.db"

# Ensure dirs exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
(MEDIA_DIR / "audio").mkdir(parents=True, exist_ok=True)
(MEDIA_DIR / "video").mkdir(parents=True, exist_ok=True)
(MEDIA_DIR / "diagrams").mkdir(parents=True, exist_ok=True)
(MEDIA_DIR / "covers").mkdir(parents=True, exist_ok=True)

# Load .env if present
env_file = BASE_DIR / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

# Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
APP_PORT = int(os.getenv("PORT", "8000"))
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Detect FFmpeg executable
FFMPEG_EXE = "ffmpeg"
try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    pass
