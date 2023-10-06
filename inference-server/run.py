import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import base64
import http.server
import json
import socketserver
from io import BytesIO
from typing import Optional

import numpy as np
import pandas as pd
from PIL import Image
from ctransformers import AutoModelForCausalLM
from translate import Translator

from model import CNeXt
from server_utils import get_tokens, split_and_translate, translate_to_english, get_recommended_video
from types_and_constants import Dialog, DEFAULT_SYSTEM_PROMPT, ImageResult
from utils import enable_memory_growth

model = None
image_model = None
plants_dataframe = None

dialog: Dialog = [
    {"role": "system", "content": DEFAULT_SYSTEM_PROMPT, },
]

translators: dict[str, Optional[Translator]] = {
    'en': None,  # bruh
}


def get_image_class_and_description(class_num: int) -> ImageResult:
    row = plants_dataframe.iloc[class_num]
    class_name = row["CLASS"]
    plant_name = row["PLANT_NAME"]
    disease_name = row["DISEASE_NAME"]
    description = row["DESCRIPTION"]
    return ImageResult(class_name, plant_name, disease_name, description)


def infer_image(image: str) -> ImageResult:
    image = base64.b64decode(image)
    image = Image.open(BytesIO(image))
    out = np.argmax(image_model.predict(np.array([image])), axis=1)
    return get_image_class_and_description(out[0])


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        input_data = self.rfile.read(content_length).decode('utf-8')
        input_json = json.loads(input_data)

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        input_message = input_json.get('message', '')
        input_image = input_json.get('image', None)
        reset_dialog = input_json.get('reset_dialog', False)
        language = input_json.get('language', 'en')
        gimme_video = True
        no_no_words = ['contain', 'image', 'picture', 'photo', 'pic', 'photo', 'show', 'display', 'hi', 'hello', 'hey',
                       'ok', 'thanks', 'you']
        if any(word in input_message.lower().split() for word in no_no_words):
            gimme_video = False
        if reset_dialog:
            dialog.clear()
            dialog.append({"role": "system", "content": DEFAULT_SYSTEM_PROMPT, })
            print('Dialog reset.')
            return
        input_message = translate_to_english(input_message)
        if gimme_video:
            video_title, video_url = get_recommended_video(input_message, language=language)
        else:
            video_title, video_url = '', ''
        if input_image is not None:
            res = infer_image(input_image)
            dialog.append({"role": "user", "content": f"{res}\n{input_message}", })
        else:
            dialog.append({"role": "user", "content": input_message, })

        out = ''
        for token in model(get_tokens(dialog), stream=True,
                           top_p=0.9, temperature=1.2, batch_size=1,
                           max_new_tokens=512, ):
            out += token
        dialog.append({"role": "assistant", "content": out, })
        # translate out
        if language != 'en':
            if language not in translators:
                translators[language] = Translator(to_lang=language)
            out = split_and_translate(out, translators[language])
        output_json = dict(message=out, video_title=video_title, video_url=video_url)
        self.wfile.write(json.dumps(output_json).encode('utf-8'))


if __name__ == "__main__":
    IP = '0.0.0.0'
    PORT = 6969

    print('Loading LLaMA...')
    model = AutoModelForCausalLM.from_pretrained("./Bloke/model.gguf",
                                                 model_type="llama",
                                                 context_length=4096,
                                                 gpu_layers=30, )
    print('LLaMA loaded.')
    print('Loading image model...')
    with open("models/num_classes.txt", "r") as f:
        num_classes = int(f.read())
    enable_memory_growth()  # enable memory growth for GPU so TensorFlow doesn't eat all the memory
    image_model = CNeXt(num_classes=num_classes)
    image_model.build((1, 256, 256, 3))
    if os.path.exists('models/CNeXt.h5'):
        image_model.load_weights('models/CNeXt.h5')
    else:
        raise FileNotFoundError('Image model weights not found.')
    print('Image model loaded.')
    print('Loading plants dataframe...')
    plants_dataframe = pd.read_csv("datasets/FARM_HUB.csv")
    print('Plants dataframe loaded.')

    with socketserver.TCPServer((IP, PORT), RequestHandler) as httpd:
        print("Server is running on port", PORT)
        httpd.serve_forever()
