from deep_translator import GoogleTranslator


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """
    Matnni source_lang'dan target_lang'ga tarjima qiladi.
    Til kodlari: uz, en, ru, tr, ar va h.k. (Google Translate kodlari)
    """
    # Google Translate'ning bepul so'rov limiti bor (juda uzun matnda xato berishi mumkin),
    # shuning uchun matnni bo'laklarga bo'lib tarjima qilamiz.
    max_chunk = 4000
    chunks = [text[i:i + max_chunk] for i in range(0, len(text), max_chunk)]

    translator = GoogleTranslator(source=source_lang, target=target_lang)
    translated_chunks = [translator.translate(chunk) for chunk in chunks]

    return " ".join(translated_chunks)
