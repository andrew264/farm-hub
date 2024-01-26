import asyncio
import json
import os

import requests
import websockets
from flask import Flask
from flask import render_template, redirect
from flask_socketio import SocketIO

from typin import Dialog, WS_EOS, ImageResult

app = Flask(__name__)
socketio = SocketIO(app)

LLM_CONVERSATION: Dialog = Dialog()

if os.path.exists('config.json'):
    with open('config.json', 'r') as f:
        config = json.load(f)
else:
    FileNotFoundError('config.json not found')

LLM_SERVER_HOST = config['llm-server']['host']
LLM_SERVER_PORT = config['llm-server']['port']
LLM_SERVER_URI = f'ws://{LLM_SERVER_HOST}:{LLM_SERVER_PORT}'
IMAGE_SERVER_HOST = config['image-server']['host']
IMAGE_SERVER_PORT = config['image-server']['port']
IMAGE_SERVER_URI = f'http://{IMAGE_SERVER_HOST}:{IMAGE_SERVER_PORT}'


async def do_llm_inference() -> str:
    async with websockets.connect(LLM_SERVER_URI, ping_interval=None) as websocket:
        await websocket.send(LLM_CONVERSATION.get_tokens())

        full_response = ''
        while True:
            response = await websocket.recv()
            if response == WS_EOS:
                break
            else:
                socketio.emit('content', response)
                full_response += response
        socketio.emit('content', WS_EOS)

    return full_response


def do_image_inference(image_b64) -> ImageResult:
    image_b64 = image_b64.split(',')[1]
    with requests.Session() as session:
        with session.post(IMAGE_SERVER_URI, json={'image': image_b64}) as resp:
            result = ImageResult.from_json(resp.json())
            return result


@app.route('/')
def index():
    LLM_CONVERSATION.reset()
    return render_template('index.html')


@app.route('/clear')
def clear():
    LLM_CONVERSATION.reset()
    return redirect('/')


@socketio.on('connect')
def handle_connect():
    print("client socket connected")


@socketio.on('disconnect')
def handle_disconnect():
    print("client socket disconnected")


@socketio.on('submit')
def handle_submit(data):
    message = data.get('message', '')
    image = data.get('image', None)
    content = message
    if image:
        image_result = do_image_inference(image)
        if image_result:
            content = f'Image: {image_result}\n{message}'
    LLM_CONVERSATION.add_user_message(content)

    resp = asyncio.new_event_loop().run_until_complete(do_llm_inference())
    LLM_CONVERSATION.add_assistant_message(resp)


if __name__ == '__main__':
    print(os.getcwd())

    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
