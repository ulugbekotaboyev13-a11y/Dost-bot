import asyncio
import subprocess
import edge_tts

# Ko'p ishlatiladigan tillar uchun edge-tts ovoz nomlari.
# To'liq ro'yxat: `edge-tts --list-voices` buyrug'i orqali ko'riladi.
VOICE_MAP = {
    "en": "en-US-GuyNeural",
    "ru": "ru-RU-DmitryNeural",
    "tr": "tr-TR-AhmetNeural",
    "ar": "ar-SA-HamedNeural",
    "es": "es-ES-AlvaroNeural",
    "fr": "fr-FR-HenriNeural",
    "de": "de-DE-ConradNeural",
    "zh-CN": "zh-CN-YunxiNeural",
    "hi": "hi-IN-MadhurNeural",
    "id": "id-ID-ArdiNeural",
    # Eslatma: edge-tts'da o'zbek tili ovozi yo'q — o'zbek tiliga dublyaj qilib bo'lmaydi,
    # lekin o'zbekchadan boshqa tillarga tarjima/dublyaj qilish muammosiz ishlaydi.
}


async def _generate_speech(text: str, voice: str, out_path: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)


def text_to_speech(text: str, target_lang: str, out_path: str):
    voice = VOICE_MAP.get(target_lang)
    if voice is None:
        raise ValueError(
            f"'{target_lang}' tili uchun ovoz topilmadi. VOICE_MAP'ga qo'shing."
        )
    asyncio.run(_generate_speech(text, voice, out_path))


def merge_audio_with_video(video_path: str, audio_path: str, out_path: str):
    """Video ichidagi asl audio'ni yangi (dublyaj qilingan) audio bilan almashtiradi."""
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            out_path,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
                          )
