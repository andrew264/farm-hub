import asyncio
import base64
import json
import os

import requests
import websockets
from flask import Flask
from flask import render_template, redirect
from flask_socketio import SocketIO

from fs_utils import DEFAULT_SYSTEM_PROMPT, get_tokens, WS_EOS
from typin import Dialog

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')

LLM_CONVERSATION: Dialog = [
    {"role": "system", "content": DEFAULT_SYSTEM_PROMPT, },
]

if os.path.exists('config.json'):
    with open('config.json', 'r') as f:
        config = json.load(f)
else:
    FileNotFoundError('config.json not found')

LLM_SERVER_HOST = config['llm-server']['host']
LLM_SERVER_PORT = config['llm-server']['port']
LLM_SERVER_URI = f'ws://{LLM_SERVER_HOST}:{LLM_SERVER_PORT}'
print(f'LLM_SERVER_URI: {LLM_SERVER_URI}')
IMAGE_SERVER_HOST = config['image-server']['host']
IMAGE_SERVER_PORT = config['image-server']['port']
IMAGE_SERVER_URI = f'http://{IMAGE_SERVER_HOST}:{IMAGE_SERVER_PORT}'
print(f'IMAGE_SERVER_URI: {IMAGE_SERVER_URI}')


async def do_llm_inference() -> str:
    async with websockets.connect(LLM_SERVER_URI) as websocket:
        await websocket.send(get_tokens(LLM_CONVERSATION))

        full_response = ''
        while True:
            response = await websocket.recv()
            if response == WS_EOS:
                break
            elif '</s>' in response:
                break
            else:
                # print(response, end='')
                socketio.emit('content', response)
                full_response += response
        socketio.emit('content', WS_EOS)

    full_response = full_response.replace('</s>', '')
    return full_response


def do_image_inference(image_bytes) -> str:
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    with requests.Session() as session:
        with session.post(IMAGE_SERVER_URI, json={'image': image_base64}) as resp:
            result = resp.json()
            if 'result' in result:
                return result['result']
            else:
                print(result)
                return 'Error'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/clear')
def clear():
    default = LLM_CONVERSATION[0]
    LLM_CONVERSATION.clear()
    LLM_CONVERSATION.append(default)
    return redirect('/')


@socketio.on('connect')
def handle_connect():
    print("Client connected ")


@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected ")


@socketio.on('submit')
def handle_submit(data):
    message = data.get('message', '')
    lang = data.get('lang', 'en')
    image = data.get('image', None)

    if image:
        image_bytes = base64.b64decode(image.split(',')[1])
        image_result = do_image_inference(image_bytes)
        LLM_CONVERSATION.append({"role": "user", "content": f'Image: {image_result}\n{message}'})
    else:
        LLM_CONVERSATION.append({"role": "user", "content": message})

    resp = asyncio.new_event_loop().run_until_complete(do_llm_inference())
    LLM_CONVERSATION.append({"role": "assistant", "content": resp})


if __name__ == '__main__':
    print(os.getcwd())

    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
