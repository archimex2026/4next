"""Optional source-language narration. Failed services never become silent 'ready' audio."""
import asyncio
import re
import subprocess
import uuid
from pathlib import Path
from app.config import MEDIA_DIR, FFMPEG_EXE

AUDIO_DIR = MEDIA_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_VOICES = {"ro":"ro-RO-AlinaNeural", "en":"en-US-JennyNeural"}


def get_audio_duration(audio_file_path):
    try:
        result = subprocess.run([FFMPEG_EXE,"-hide_banner","-i",str(audio_file_path)],
            capture_output=True,text=True,errors="replace",timeout=5)
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)",result.stderr)
        if match:
            hours,minutes,seconds = map(float,match.groups())
            return round(hours*3600+minutes*60+seconds,2)
    except (OSError,subprocess.TimeoutExpired):
        pass
    return 0.0


async def _edge(script,voice,rate,path):
    import edge_tts
    await asyncio.wait_for(edge_tts.Communicate(script,voice=voice,rate=rate).save(str(path)),timeout=45)


def _synthesize(script,voice,rate,language,path):
    try:
        asyncio.run(_edge(script,voice,rate,path))
    except Exception:
        path.unlink(missing_ok=True)
        from gtts import gTTS
        gTTS(text=script,lang=language,timeout=(5,15)).save(str(path))
    if not path.is_file() or path.stat().st_size < 1000:
        raise RuntimeError("Narration service returned no usable audio.")


def generate_audio_lesson(lesson_id,title,summary,key_ideas,examples,long_explanation="",
    practical_insights=None,action_items=None,conclusion="",lang="ro",voice=None,rate="+0%",
    custom_script="",return_details=False):
    if lang not in DEFAULT_VOICES or not re.fullmatch(r"[A-Za-z0-9_-]+",lesson_id):
        raise ValueError("Unsupported language or lesson identifier")
    if custom_script:
        raise ValueError("Only the source-backed lesson can be narrated")
    voice = voice or DEFAULT_VOICES[lang]
    if not voice.startswith(lang+"-"):
        raise ValueError("The voice must match the document language")
    parts = [title, long_explanation or summary, *(key_ideas or []), *(examples or []),
        *(practical_insights or []), *(action_items or [])]
    script = "\n\n".join(dict.fromkeys(str(part).strip() for part in parts if str(part or "").strip()))
    if not script or len(script)>30000:
        raise ValueError("Narration must contain between 1 and 30000 characters")
    output = AUDIO_DIR / f"{lesson_id}_{lang}.mp3"
    temporary = AUDIO_DIR / f".{lesson_id}-{uuid.uuid4().hex}.mp3"
    try:
        _synthesize(script,voice,rate,lang,temporary)
        duration = get_audio_duration(temporary) or max(1,round(len(script.split())/2.5,1))
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    scenes = [{"scene":1,"title":title,"timestamp":"0:00","duration_sec":duration,"speaker":script}]
    url = f"/media/audio/{output.name}"
    return (url,duration,scenes) if return_details else url

