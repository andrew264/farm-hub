import base64
import http.server
import io
import json
import os
import signal
import socketserver
import sys

import numpy as np
import pandas as pd
from PIL import Image

from _types import ImageResult

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

image_classifier = None
plants_dataframe = pd.read_csv("datasets/FARM_HUB.csv")


def do_image_inference(image_base64: str) -> ImageResult:
    image_bytes = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(image_bytes))
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


class ImageInferenceRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            request_data = json.loads(post_data.decode('utf-8'))
            image_base64 = request_data.get("image", None)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            if image_base64 is not None:
                image_result = do_image_inference(image_base64)
                response = {'result': str(image_result)}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                error_message = {"error": "Image not found"}
                self.wfile.write(json.dumps(error_message).encode('utf-8'))
        except json.JSONDecodeError as e:
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            error_message = {"error": "Invalid Image input"}
            self.wfile.write(json.dumps(error_message).encode('utf-8'))


if __name__ == "__main__":
    with open('config.json') as f:
        config = json.load(f)
    host = config['image-server']['host']
    port = config['image-server']['port']
    server = socketserver.TCPServer((host, port), ImageInferenceRequestHandler)


    def signal_handler(sig, frame):
        # Handle Ctrl+C by gracefully shutting down the server
        print("Shutting down the server")
        server.socket.close()
        sys.exit(0)


    print('Loading Image Classifier...')
    import tensorflow as tf
    from model import CNeXt

    with open("models/num_classes.txt", "r") as f:
        num_classes = int(f.read())

    with tf.device('/cpu:0'):
        image_classifier = CNeXt(num_classes=num_classes)
        image_classifier.build((1, 256, 256, 3))
        if os.path.exists('models/CNeXt.h5'):
            image_classifier.load_weights('models/CNeXt.h5')
        else:
            raise FileNotFoundError('Model weights not found.')
        image_classifier.predict(np.zeros((1, 256, 256, 3)))

    # Start the server
    print("Press Ctrl+C to stop the server")
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    print(f"Server listening on http://{host}:{port}")
    server.serve_forever()
