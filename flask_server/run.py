import aiohttp
import base64
import os
import shutil

import flask
from flask import request, render_template, send_from_directory

app = flask.Flask(__name__)

chat_messages = []
CACHE_DIR = 'temp-files'
app.config['UPLOAD_FOLDER'] = CACHE_DIR


async def get_inference_output():
    message, image = chat_messages[-1][1:]
    if image == '':
        image = None
    else:
        with open(os.path.join('flask_server', CACHE_DIR, image), 'rb') as f:
            image = base64.b64encode(f.read()).decode('utf-8')
    input_data = {'message': message, 'image': image}
    async with aiohttp.ClientSession() as session:
        r = await session.post('http://localhost:8000/inference', json=input_data)
        chat_messages.append(('bot', await r.text(), ''))
        print(chat_messages[-1])


async def reset_dialog():
    chat_messages.clear()
    input_data = {'reset_dialog': True}
    async with aiohttp.ClientSession() as session:
        r = await session.post('http://localhost:8000/inference', json=input_data)
        print(await r.text())


@app.route('/')
async def index():
    return render_template('index.html', chat_messages=chat_messages)


@app.route('/<path:name>')
async def download_file(name):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'], name, as_attachment=True
    )


@app.route('/upload', methods=['POST'])
async def upload():
    message = request.form.get('message', '')

    if 'file' in request.files:
        image = request.files['file']

        if image.filename != '':
            # generate a random filename
            file_format = image.filename.split('.')[-1]
            filename = f'{os.urandom(16).hex()}.{file_format}'
            image.save(os.path.join('flask_server', CACHE_DIR, filename))
            chat_messages.append(('user', message, filename))
        else:
            chat_messages.append(('user', message, ''))
    await get_inference_output()

    return render_template('index.html', chat_messages=chat_messages)


if __name__ == '__main__':

    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)

    os.mkdir(CACHE_DIR)

    app.run(port=5000, debug=True)
