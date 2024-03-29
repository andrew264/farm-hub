import asyncio
import json
import os
import sys

import path
import pytube
import requests
import websockets
from flask import Flask, jsonify
from flask import render_template, redirect, request, flash, make_response
from flask_socketio import SocketIO

sys.path.append(path.Path(__file__).abspath().parent.parent)

from typin import Dialog, WS_EOS, ImageResult

app = Flask(__name__)
app.secret_key = "akjhasbd,as"
socketio = SocketIO(app)

# modern user database
users_path = os.path.join(os.path.dirname(__file__), 'static/assets/users.json')
users = {}
with open(users_path, 'r') as f:
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

EMBED_TEMPLATE = ("<span>Here is a recommended video:&nbsp;</span><a href='{url}' target='_blank'>{title}</a>"
                  "<span>&nbsp;I hope it helps.</span>")


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


def do_image_inference(image_b64) -> ImageResult:
    image_b64 = image_b64.split(',')[1]
    with requests.Session() as session:
        with session.post(IMAGE_SERVER_URI, json={'image': image_b64}) as resp:
            result = ImageResult.from_json(resp.json())
            return result


@app.route('/get_video_embed')
def get_video_embed() -> str:
    username = request.cookies.get('username', None)
    if username is None:
        return ""
    conversation = LLM_CONVERSATION.get(username, None)
    if conversation is None:
        return ""
    context = conversation.context
    res = pytube.contrib.search.Search(context)
    if res.results:
        video = res.results[0]
        return EMBED_TEMPLATE.format(title=video.title, url=video.watch_url)
    else:
        return ""


@app.route('/')
def landing():
    return render_template('landingPage.html')


@app.route('/llm-chat')
def llm_chat():
    username = request.cookies.get('username', None)
    if username is None:
        return redirect('/login')
    LLM_CONVERSATION[username] = Dialog()
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('pwd')

        if username not in users:
            users[username] = password
            # update users.json
            with open(users_path, 'w') as f_:
                json.dump(users, f_, indent=4)

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
            # create a cookie
            resp = make_response(redirect('/llm-chat'))
            resp.set_cookie('username', username, max_age=60 * 60)

            flash("You were successfully logged in")
            return resp

        else:
            return "Invalid username or password!"
    return render_template('login.html')


@app.route('/get_username')
def get_username():
    username = request.cookies.get('username')
    return jsonify({'username': username})


@app.route('/clear')
def clear():
    conversation = LLM_CONVERSATION.get('default')
    conversation.reset()
    return redirect('/llm-chat')


@socketio.on('connect')
def handle_connect():
    print("client socket connected")


@socketio.on('disconnect')
def handle_disconnect():
    print("client socket disconnected")


@socketio.on('submit')
def handle_submit(data):
    username = request.cookies.get('username', None)
    if username is None:
        return redirect('/login')
    conversation = LLM_CONVERSATION.get(username, None)
    if conversation is None:
        return redirect('/login')
    message = data.get('message', '')
    image = data.get('image', None)
    language = data.get('language', 'English')
    content = message
    conversation.context = message
    conversation.user_language = language
    if image:
        image_result = do_image_inference(image)
        conversation.image_class = image_result.class_name
        if image_result:
            content = f'Image: {image_result}\n{message}'
    if image is None and message != "":
        conversation.image_class = ""
    conversation.add_user_message(content)

    resp = asyncio.new_event_loop().run_until_complete(do_llm_inference(conversation))
    conversation.add_assistant_message(resp)


if __name__ == '__main__':
    print(os.getcwd())

    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
