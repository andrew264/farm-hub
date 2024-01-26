import http.server
import json
import os
import random
import signal
import socketserver
import sys

import pandas as pd

from _types import ImageResult

image_classifier = None
plants_dataframe = pd.read_csv("datasets/FARM_HUB.csv")


def do_image_inference(image_base64: str) -> ImageResult:
    print("Received image: ", image_base64)

    out = random.randint(0, plants_dataframe.shape[0] - 1)
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
                print("No image found")
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
    print("Starting server...")
    server = socketserver.TCPServer((host, port), ImageInferenceRequestHandler)


    def signal_handler(sig, frame):
        # Handle Ctrl+C by gracefully shutting down the server
        print("Shutting down the server")
        server.socket.close()
        sys.exit(0)

    # Start the server
    print("Press Ctrl+C to stop the server")
    if os.name == 'posix':
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    else:
        print("WARNING: Cannot add signal handlers on non-Linux OS")
    print(f"Server listening on http://{host}:{port}")
    server.serve_forever()
