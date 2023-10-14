import asyncio
import json
import signal

import websockets
from ctransformers import AutoModelForCausalLM

from types_and_constants import WS_EOS

llm = None


async def handle_client(websocket):
    try:
        while True:
            # Receive a string input from the client
            client_input = await websocket.recv()
            print("Processing input...")

            generated = ''
            # Send the input to the model and get the output
            for token in llm(client_input, stream=True,
                             top_p=0.9, temperature=1.2, batch_size=1,
                             max_new_tokens=512, ):
                generated += token
                await websocket.send(token)
                if '</s>' in generated:
                    break

            # send eos
            await websocket.send(WS_EOS)

    except websockets.ConnectionClosedError:
        print("Client disconnected")
    except websockets.ConnectionClosedOK:
        print("Client disconnected")


async def start_server(host: str, port: int):
    loop = asyncio.get_event_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)
    print("Press Ctrl+C to stop the server")
    print(f"Server Listening on {host}:{port}")

    async with websockets.serve(handle_client, host, port):
        await stop


if __name__ == "__main__":
    print("Loading LLM...")
    llm = AutoModelForCausalLM.from_pretrained("Bloke/model.gguf",
                                               model_type="llama",
                                               context_length=4096,
                                               gpu_layers=30, )
    print("Starting server...")
    with open('config.json') as f:
        config = json.load(f)
    host = config['llm-server']['host']
    port = config['llm-server']['port']

    asyncio.run(start_server(host, port))