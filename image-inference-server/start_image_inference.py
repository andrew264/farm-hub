import base64
import http.server
import io
import json
import os
import signal
import socketserver
import sys

import pandas as pd
import torch
from PIL import Image
from torchvision import transforms

from typin import ImageResult

image_classifier = None
plants_dataframe = pd.read_csv("datasets/FARM_HUB.csv")
model_path = "models/convnext_small.pth"
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


def do_image_inference(image_base64: str) -> ImageResult:
    image_bytes = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image_tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        out = image_classifier(image_tensor)
        _, predicted = torch.max(out.data, 1)
    out = predicted.item()
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
                self.wfile.write(image_result.to_json().encode('utf-8'))
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
    device = torch.device("cpu")
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
    from model import CNeXt

    with open("models/num_classes.txt", "r") as f:
        num_classes = int(f.read())
        image_classifier = CNeXt(num_classes=num_classes)
        image_classifier.to(device=device)
        if os.path.exists(model_path):
            image_classifier.load_state_dict(torch.load(model_path, map_location=device))
        else:
            raise FileNotFoundError('Model weights not found.')
        image_classifier.eval()

    # Start the server
    print("Press Ctrl+C to stop the server")
    if os.name == 'posix':
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    else:
        print("WARNING: Cannot add signal handlers on non-Linux OS")
    print(f"Server listening on http://{host}:{port}")
    server.serve_forever()
