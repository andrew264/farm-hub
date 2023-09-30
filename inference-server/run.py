import http.server
import json
import socketserver

from ctransformers import AutoModelForCausalLM

from types_and_constants import PORT, Dialog, DEFAULT_SYSTEM_PROMPT
from utils import get_tokens

model = None

dialog: Dialog = [
    {"role": "system", "content": DEFAULT_SYSTEM_PROMPT, },
]


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        input_data = self.rfile.read(content_length).decode('utf-8')
        input_json = json.loads(input_data)

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        input_message = input_json['message']
        dialog.append({"role": "user", "content": input_message, })

        out = ''
        for token in model(get_tokens(dialog), stream=True,
                           top_p=0.9, temperature=1.2, batch_size=1,
                           max_new_tokens=512, ):
            out += token
            self.wfile.write(token.encode('utf-8'))
        dialog.append({"role": "assistant", "content": out, })


if __name__ == "__main__":
    print('Loading model...')
    model = AutoModelForCausalLM.from_pretrained("../Bloke/model.gguf",
                                                 model_type="llama",
                                                 context_length=4096,
                                                 gpu_layers=30, )
    print('Model loaded.')
    with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
        print("Server is running on port", PORT)
        httpd.serve_forever()
