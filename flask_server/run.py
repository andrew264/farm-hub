import base64
import os
from io import BytesIO

import flask
import numpy as np
import pandas as pd
from PIL import Image
from flask import render_template, request, redirect

from typin import RenderObj, ImageResult

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

app = flask.Flask(__name__)

chat_messages: list[RenderObj] = []
image_classifier = None
plants_dataframe = pd.read_csv("../datasets/FARM_HUB.csv")


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
        print(image_result)
    else:
        image_base64 = None

    chat_messages.append(RenderObj(content=message, lang=lang, image_base64=image_base64, sender='user'))

    return redirect('/')


if __name__ == '__main__':
    print(os.getcwd())
    print('Loading image classifier...')
    image_classifier = load_image_classifier()
    do_dummy_inference()

    app.run(host='0.0.0.0', port=5000, debug=True)
