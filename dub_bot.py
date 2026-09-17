import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile, BufferedInputFile
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from transcribe import extract_audio, transcribe
from translate import translate_text
from tts_dub import text_to_speech, merge_audio_with_video, VOICE_MAP
from subtitles import segments_to_srt, burn_subtitles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Har bir foydalanuvchining videosi shu yerda vaqtincha saqlanadi (video_path)
user_videos: dict[int, str] = {}

LANG_NAMES = {
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
    "tr": "🇹🇷 Türkçe",
    "ar": "🇸🇦 العربية",
    "es": "🇪🇸 Español",
    "id": "🇮🇩 Indonesia",
}


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Salom! Menga video yuboring — subtitr yozib beraman yoki boshqa tilga "
        "dublyaj qilib beraman."
    )


@dp.message(F.video | F.document)
async def handle_video(message: Message):
    user_id = message.from_user.id

    file_obj = message.video or message.document
    if message.document and not (message.document.mime_type or "").startswith("video/"):
        await message.answer("Iltimos, video fayl yuboring.")
        return

    file = await bot.get_file(file_obj.file_id)
    os.makedirs("downloads", exist_ok=True)
    video_path = f"downloads/{user_id}_{file_obj.file_unique_id}.mp4"
    await bot.download_file(file.file_path, video_path)

    user_videos[user_id] = video_path

    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Subtitr qo'sh", callback_data="action:subtitle")
    builder.button(text="🌍 Tilini o'zgartir (dublyaj)", callback_data="action:dub")
    builder.adjust(1)

    await message.answer("Video qabul qilindi. Nima qilay?", reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("action:"))
async def handle_action_choice(callback: CallbackQuery):
    action = callback.data.split(":")[1]
    await callback.answer()

    if action == "subtitle":
        await callback.message.edit_text("Subtitr tayyorlanmoqda, biroz kuting... ⏳")
        await process_subtitle(callback)
    elif action == "dub":
        builder = InlineKeyboardBuilder()
        for code, name in LANG_NAMES.items():
            builder.button(text=name, callback_data=f"lang:{code}")
        builder.adjust(2)
        await callback.message.edit_text(
            "Qaysi tilga o'girib beray?", reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data.startswith("lang:"))
async def handle_lang_choice(callback: CallbackQuery):
    target_lang = callback.data.split(":")[1]
    await callback.answer()

    if target_lang not in VOICE_MAP:
        await callback.message.edit_text("Kechirasiz, bu til uchun ovoz hali qo'llab-quvvatlanmaydi.")
        return

    await callback.message.edit_text("Dublyaj tayyorlanmoqda, bu biroz vaqt olishi mumkin... ⏳")
    await process_dub(callback, target_lang)


async def process_subtitle(callback: CallbackQuery):
    user_id = callback.from_user.id
    video_path = user_videos.get(user_id)
    if not video_path:
        await callback.message.answer("Avval video yuboring.")
        return

    audio_path = video_path.replace(".mp4", ".wav")
    srt_path = video_path.replace(".mp4", ".srt")
    out_path = video_path.replace(".mp4", "_sub.mp4")

    try:
        extract_audio(video_path, audio_path)
        _, segments, _ = transcribe(audio_path)
        segments_to_srt(segments, srt_path)
        burn_subtitles(video_path, srt_path, out_path)

        await bot.send_video(
            chat_id=user_id, video=FSInputFile(out_path), caption="Tayyor! 🎬"
        )
    except Exception as e:
        logger.exception("Subtitr xatosi")
        await bot.send_message(chat_id=user_id, text=f"Xatolik yuz berdi: {e}")
    finally:
        for p in (audio_path, srt_path, out_path):
            if os.path.exists(p):
                os.remove(p)


async def process_dub(callback: CallbackQuery, target_lang: str):
    user_id = callback.from_user.id
    video_path = user_videos.get(user_id)
    if not video_path:
        await callback.message.answer("Avval video yuboring.")
        return

    audio_path = video_path.replace(".mp4", ".wav")
    tts_path = video_path.replace(".mp4", f"_{target_lang}.mp3")
    out_path = video_path.replace(".mp4", f"_dub_{target_lang}.mp4")

    try:
        extract_audio(video_path, audio_path)
        text, _, detected_lang = transcribe(audio_path)
        translated = translate_text(text, source_lang=detected_lang, target_lang=target_lang)
        text_to_speech(translated, target_lang, tts_path)
        merge_audio_with_video(video_path, tts_path, out_path)

        await bot.send_video(
            chat_id=user_id, video=FSInputFile(out_path), caption="Tayyor! 🎬"
        )
    except Exception as e:
        logger.exception("Dublyaj xatosi")
        await bot.send_message(chat_id=user_id, text=f"Xatolik yuz berdi: {e}")
    finally:
        for p in (audio_path, tts_path, out_path):
            if os.path.exists(p):
                os.remove(p)


async def main():
    logger.info("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
