import base64
import os
from io import BytesIO

import numpy as np
import pandas as pd
import websockets
from PIL import Image
from flask import Flask
from flask import render_template, request, redirect
from flask_socketio import SocketIO

from fs_utils import DEFAULT_SYSTEM_PROMPT, get_tokens, WS_EOS
from typin import RenderObj, ImageResult, Dialog

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

app = Flask(__name__)
socketio = SocketIO(app)

chat_messages: list[RenderObj] = []
image_classifier = None
plants_dataframe = pd.read_csv("../datasets/FARM_HUB.csv")
LLM_SERVER_URI = "ws://localhost:8765"

LLM_CONVERSATION: Dialog = [
    {"role": "system", "content": DEFAULT_SYSTEM_PROMPT, },
]


def load_image_classifier():
    import tensorflow as tf
    from model import CNeXt

    with open("../models/num_classes.txt", "r") as f:
        num_classes = int(f.read())

    with tf.device('/cpu:0'):
        model = CNeXt(num_classes=num_classes)
        model.build((1, 256, 256, 3))
        if os.path.exists('../models/CNeXt.h5'):
            model.load_weights('../models/CNeXt.h5')
        else:
            raise FileNotFoundError('Image model weights not found.')
    return model


def do_dummy_inference():
    image_classifier.predict(np.zeros((1, 256, 256, 3)))


def do_image_inference(image_bytes: bytes) -> ImageResult:
    image = Image.open(BytesIO(image_bytes))
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image = image.resize((256, 256))
    out = np.argmax(image_classifier.predict(np.array([image]), verbose=0), axis=1)[0]
    row = plants_dataframe.iloc[out]
    class_name = row["CLASS"]
    plant_name = row["PLANT_NAME"]
    disease_name = row["DISEASE_NAME"]
    description = row["DESCRIPTION"]
    return ImageResult(class_name, plant_name, disease_name, description)


async def do_llm_inference():
    async with websockets.connect(LLM_SERVER_URI) as websocket:
        await websocket.send(get_tokens(LLM_CONVERSATION))

        full_response = ''
        while True:
            response = await websocket.recv()
            if response == WS_EOS:
                break
            else:
                # print(response, end='')
                socketio.emit('content', response)
                full_response += response

        LLM_CONVERSATION.append({"role": "assistant", "content": full_response})
        chat_messages.append(RenderObj(content=full_response, lang='en', image_base64=None, sender='bot'))


@app.route('/')
async def index():
    return render_template('index.html', messages=chat_messages)


@app.route('/submit', methods=['POST'])
async def submit():
    message = request.form.get('message', '')
    lang = request.form.get('lang', 'en')
    image = request.files.get('image', None)

    if image:
        print(image)
        image = request.files['image']
        file_format = image.filename.split('.')[-1]
        image_bytes = image.read()
        image_base64 = f'data:image/{file_format};base64,' + base64.b64encode(image_bytes).decode('utf-8')
        # print(image_base64[:100] + '...')
        image_result = do_image_inference(image_bytes)
        LLM_CONVERSATION.append({"role": "user", "content": f'Image: {image_result}\n{message}'})
    else:
        image_base64 = None
        LLM_CONVERSATION.append({"role": "user", "content": message})

    chat_messages.append(RenderObj(content=message, lang=lang, image_base64=image_base64, sender='user'))
    await do_llm_inference()

    return redirect('/')


@app.route('/clear')
def clear():
    default = LLM_CONVERSATION[0]
    LLM_CONVERSATION.clear()
    LLM_CONVERSATION.append(default)
    chat_messages.clear()
    return redirect('/')


@socketio.on('connect')
def handle_connect():
    print("Client connected ")


if __name__ == '__main__':
    print(os.getcwd())
    print('Loading image classifier...')
    image_classifier = load_image_classifier()
    do_dummy_inference()

    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
