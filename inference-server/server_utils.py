import re
from typing import Tuple

from langdetect import detect
from translate import Translator
from youtubesearchpython import VideosSearch

from types_and_constants import Dialog, BOS, EOS, B_INST, E_INST, B_SYS, E_SYS


def get_tokens(dialog: Dialog) -> str:
    if dialog[0]["role"] == "system":
        dialog = [
                     {
                         "role": dialog[1]["role"],
                         "content": B_SYS + dialog[0]["content"] + E_SYS + dialog[1]["content"],
                     }
                 ] + dialog[2:]

    dialog_tokens = sum(
        [
            [f"{BOS}{B_INST} {(prompt['content']).strip()} {E_INST} {(answer['content']).strip()}{EOS}"]
            for prompt, answer in zip(dialog[::2], dialog[1::2], )
        ],
        [],
    )
    dialog_tokens += f"{BOS}{B_INST} {(dialog[-1]['content']).strip()} {E_INST}{EOS}",
    return ''.join(dialog_tokens)


def split_and_translate(input_text: str, translator: Translator, max_chunk_length: int = 480) -> str:
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
    }
    result = VideosSearch(title + f" in {language_code_to_language[language]}", limit=1).result()
    video_title = result["result"][0]["title"]
    video_id = result["result"][0]["id"]
    embed_url = f"https://www.youtube.com/embed/{video_id}"
    return video_title, embed_url
