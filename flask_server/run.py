import os
import shutil

import flask
from flask import request, render_template, send_from_directory

app = flask.Flask(__name__)

chat_messages = []
CACHE_DIR = 'temp-files'
app.config['UPLOAD_FOLDER'] = CACHE_DIR


@app.route('/')
def index():
    return render_template('index.html', chat_messages=chat_messages)


@app.route('/<path:name>')
def download_file(name):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'], name, as_attachment=True
    )


@app.route('/upload', methods=['POST'])
def upload():
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

    return render_template('index.html', chat_messages=chat_messages)


if __name__ == '__main__':

    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)

    os.mkdir(CACHE_DIR)

    app.run(port=5000, debug=True)
