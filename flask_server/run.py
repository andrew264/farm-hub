import base64
import json
import os
import shutil

import flask
import httpx
from flask import request, render_template, send_from_directory, redirect

app = flask.Flask(__name__)

chat_messages = []
CACHE_DIR = 'temp-files'
app.config['UPLOAD_FOLDER'] = CACHE_DIR
CONFIG = 'config.json'
IP = 'localhost'
PORT = 8000
if os.path.exists(CONFIG):
    with open(CONFIG, 'r') as c:
        config = json.load(c)
        IP = config.get('ip', IP)
        PORT = config.get('port', PORT)
else:
    with open(CONFIG, 'w') as c:
        json.dump({'ip': IP, 'port': PORT}, c, indent=4)
INFERENCE_SERVER_URL = f'http://{IP}:{PORT}/'


async def get_inference_output(language = 'en'):
    message, image = chat_messages[-1][1:]
    if image == '':
        image = None
    else:
        with open(os.path.join('flask_server', CACHE_DIR, image), 'rb') as f:
            image = base64.b64encode(f.read()).decode('utf-8')
    input_data = {'message': message, 'image': image, 'language': language}
    output_text = ''
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(INFERENCE_SERVER_URL, json=input_data, timeout=40.0)

            if response.status_code == 200:
                async for chunk in response.aiter_bytes(1):
                    if chunk:
                        # print(chunk.decode('utf-8'), end="", flush=True)
                        output_text += chunk.decode('utf-8', errors='ignore')
            else:
                print(f"Request failed with status code {response.status_code}: {response.text}")
        except httpx.TimeoutException as exc:
            print(f"Request timed out: {exc}")

    chat_messages.append(('bot', output_text, ''))


async def reset_dialog():
    chat_messages.clear()
    input_data = {'reset_dialog': True}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(SERVER_URL, json=input_data, timeout=4.0)
            print(response.status_code, response.text)
        except httpx.TimeoutException as exc:
            print(f"Request timed out: {exc}")


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
    langSelect = request.form.get('langSelect', 'No Lang')

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
    await get_inference_output(langSelect)

    return redirect('/')


@app.route('/reset', methods=['POST'])
async def reset():
    await reset_dialog()
    return redirect('/')


if __name__ == '__main__':

    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)

    os.mkdir(CACHE_DIR)

    app.run(host='0.0.0.0', port=5000,)
