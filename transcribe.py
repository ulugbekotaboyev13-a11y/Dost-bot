import subprocess
from faster_whisper import WhisperModel

# "small" model — Railway'ning cheklangan CPU/RAM resurslari uchun optimal muvozanat.
# Tezlik kerak bo'lsa "base"ga, sifat kerak bo'lsa "medium"ga o'zgartiring.
_model = None


def get_model():
    global _model
    if _model is None:
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    return _model


def extract_audio(video_path: str, audio_path: str):
    """Videodan audio (wav) ajratib oladi."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            audio_path,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def transcribe(audio_path: str, source_lang: str | None = None):
    """
    Audio faylni matnga aylantiradi.
    Qaytaradi: (to'liq matn, segmentlar ro'yxati [(start, end, text), ...])
    source_lang berilmasa, Whisper tilni o'zi aniqlaydi.
    """
    model = get_model()
    segments, info = model.transcribe(audio_path, language=source_lang, vad_filter=True)

    full_text = []
    seg_list = []
    for seg in segments:
        full_text.append(seg.text.strip())
        seg_list.append((seg.start, seg.end, seg.text.strip()))

    return " ".join(full_text), seg_list, info.language
