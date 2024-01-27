import asyncio
import json
import os
import sys
from typing import Optional

import path
import pytube
import requests
import websockets
from flask import Flask
from flask import render_template, redirect, request, flash
from flask_socketio import SocketIO

sys.path.append(path.Path(__file__).abspath().parent.parent)

from typin import Dialog, WS_EOS, ImageResult

app = Flask(__name__)
app.secret_key = "akjhasbd,as"
socketio = SocketIO(app)

users = {}

with open('flask_server/static/assets/users.json', 'r') as f:
    users = json.load(f)


LLM_CONVERSATION: dict[str, Dialog] = {"default": Dialog()}

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


async def do_llm_inference(conversation: Dialog) -> str:
    async with websockets.connect(LLM_SERVER_URI, ping_interval=None) as websocket:
        await websocket.send(conversation.get_tokens())

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


def get_video_link(context: str) -> Optional[str]:
    res = pytube.contrib.search.Search(context)
    if res.results:
        return 'https://www.youtube.com/embed/' + res.results[0].video_id
    else:
        return None


def do_image_inference(image_b64) -> ImageResult:
    image_b64 = image_b64.split(',')[1]
    with requests.Session() as session:
        with session.post(IMAGE_SERVER_URI, json={'image': image_b64}) as resp:
            result = ImageResult.from_json(resp.json())
            return result

@app.route('/')
def landing():
    return render_template('landingPage.html')

@app.route('/llm-chat')
def llm_chat():
    # create a conversation here
    if 'default' not in LLM_CONVERSATION:
        LLM_CONVERSATION['default'] = Dialog()
    conversation = LLM_CONVERSATION.get('default')
    conversation.reset()
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('pwd')

        if username not in users:
            users[username] = password
            with open('flask_server/static/assets/users.json', 'w') as f:
                json.dump(users, f)
            return redirect('/login')
        else:
            flash("Username already exists!")
            return redirect('/register')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if users.get(username) == password:
            flash("You were successfully logged in")
            return redirect('/llm-chat')

        else:
            return "Invalid username or password!"
    return render_template('login.html')


@app.route('/clear')
def clear():
    conversation = LLM_CONVERSATION.get('default')
    conversation.reset()
    return redirect('/')


@socketio.on('connect')
def handle_connect():
    print("client socket connected")


@socketio.on('disconnect')
def handle_disconnect():
    print("client socket disconnected")

@socketio.on('submit')
def handle_submit(data):
    conversation = LLM_CONVERSATION.get('default')
    message = data.get('message', '')
    image = data.get('image', None)
    content = message
    conversation.context = message
    if image:
        image_result = do_image_inference(image)
        conversation.image_class = image_result.class_name
        if image_result:
            content = f'Image: {image_result}\n{message}'
    conversation.add_user_message(content)

    resp = asyncio.new_event_loop().run_until_complete(do_llm_inference(conversation))
    conversation.add_assistant_message(resp)


if __name__ == '__main__':
    print(os.getcwd())

    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
