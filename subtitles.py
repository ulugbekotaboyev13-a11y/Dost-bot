import subprocess


def _format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def segments_to_srt(segments, srt_path: str):
    """segments: [(start, end, text), ...] ro'yxatidan .srt fayl yasaydi."""
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, (start, end, text) in enumerate(segments, start=1):
            f.write(f"{i}\n")
            f.write(f"{_format_timestamp(start)} --> {_format_timestamp(end)}\n")
            f.write(f"{text}\n\n")


def burn_subtitles(video_path: str, srt_path: str, out_path: str):
    """Subtitrni to'g'ridan-to'g'ri video kadrlariga yozib qo'yadi (burn-in)."""
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"subtitles={srt_path}",
            "-c:a", "copy",
            out_path,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
