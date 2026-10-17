import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
# Separate demo instances must never reuse local users, uploads, or media.
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR))).expanduser().resolve()
UPLOAD_DIR = DATA_DIR / "uploads"
MEDIA_DIR = DATA_DIR / "media"

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
                os.environ.setdefault(k.strip(), v.strip())

# Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DB_PATH = Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "book2course.db"))).expanduser().resolve()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
APP_PORT = int(os.getenv("PORT", "8000"))
DATABASE_URL = f"sqlite:///{DB_PATH}"
ALLOWED_ORIGINS = [value.strip().rstrip("/") for value in os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",") if value.strip() and value.strip() != "*"]
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
SESSION_COOKIE_NAME = "four_next_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 14

# Detect FFmpeg executable
FFMPEG_EXE = "ffmpeg"
try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    pass
