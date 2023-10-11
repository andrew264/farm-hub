import re
from typing import Tuple

from langdetect import detect
from translate import Translator
from youtubesearchpython import VideosSearch


def split_and_translate(input_text: str, translator: Translator, max_chunk_length: int = 480) -> str:
    if len(input_text) <= 6:
        return input_text
    if len(input_text) <= max_chunk_length:
        return translator.translate(input_text)
    # Split input text into sentences
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', input_text)

    # Initialize variables
    current_chunk = ""
    translated_chunks = []

    for sentence in sentences:
        # If adding the next sentence doesn't exceed the max_chunk_length, add it to the current_chunk
        if len(current_chunk) + len(sentence) + 1 <= max_chunk_length:
            current_chunk += " " + sentence if current_chunk else sentence
        else:
            # Translate the current chunk
            translated_chunk = translator.translate(current_chunk)

            # Append the translated chunk to the result
            translated_chunks.append(translated_chunk)

            # Start a new chunk with the current sentence
            current_chunk = sentence

    # Translate and append the last chunk
    translated_chunk = translator.translate(current_chunk)
    translated_chunks.append(translated_chunk)

    # Combine the translated chunks into a single output
    translated_output = " ".join(translated_chunks)

    return translated_output


def translate_to_english(text: str) -> str:
    if len(text) <= 6:
        return text
    # Detect the language of the input text
    detected_language = detect(text)
    print(f"Detected language: {detected_language}")

    # If the detected language is not English, translate to English
    if detected_language != "en":
        translator = Translator(to_lang="en", from_lang=detected_language)
        translated_text = translator.translate(text)
        print(f"Translated text: {translated_text}")
        return translated_text
    else:
        return text


def get_recommended_video(title: str, language: str = 'en') -> Tuple[str, str]:
    """
    Recommend a video based on the title
    :param title: Title of the video
    :param language: Language of the video
    :return: Tuple of video title and Embed URL
    """
    if len(title) <= 6:
        return '', ''
    language_code_to_language = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'hi': 'Hindi',
        'bn': 'Bengali',
        'te': 'Telugu',
        'ta': 'Tamil',
        'mr': 'Marathi',
        'ur': 'Urdu',
        'gu': 'Gujarati',
        'kn': 'Kannada',
        'ml': 'Malayalam',
        'pa': 'Punjabi',
        'ja': 'Japanese',
        'ar': 'Arabic',
        'zh': 'Chinese',
    }
    result = VideosSearch(title + f" in {language_code_to_language[language]}", limit=1).result()
    video_title = result["result"][0]["title"]
    video_id = result["result"][0]["id"]
    embed_url = f"https://www.youtube.com/embed/{video_id}"
    return video_title, embed_url
