import asyncio
import json
import os
import signal

import websockets
from vllm import AsyncEngineArgs, AsyncLLMEngine, SamplingParams

from types_and_constants import WS_EOS

engine = None
path = "/mnt/d/Llama-2-7B-Chat-AWQ"
sampling_params = SamplingParams(temperature=0.8, top_p=0.95, max_tokens=256)


async def handle_client(websocket: websockets.WebSocketServerProtocol, path: str = None):
    try:
        while True:
            # Receive a string input from the client
            client_input = await websocket.recv()
            print("Processing input...")

            last_index = 0
            # Send the input to the model and get the output
            async for output in engine.generate(client_input, sampling_params, request_id="INFERENCE-SERVER"):
                await websocket.send(output.outputs[0].text[last_index:])
                last_index = len(output.outputs[0].text)
            await websocket.send(WS_EOS)

            # send eos
            pong_waiter = await websocket.ping()
            latency = await pong_waiter
            print(f"Latency: {latency * 1000:.4f}ms")
            await websocket.send(WS_EOS)

    except websockets.ConnectionClosedError:
        print("Client disconnected with error")
    except websockets.ConnectionClosedOK:
        print("Client disconnected OK")


async def start_server(host: str, port: int):
    loop = asyncio.get_event_loop()
    stop = loop.create_future()
    if os.name == 'posix':
        loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
        loop.add_signal_handler(signal.SIGINT, stop.set_result, None)
    else:
        print("WARNING: Cannot add signal handlers on non-Linux OS")
    print("Press Ctrl+C to stop the server")
    print(f"Server Listening on {host}:{port}")

    async with websockets.serve(handle_client, host, port, ping_interval=None):
        await stop


if __name__ == "__main__":
    print("Loading LLM...")
    engine_args = AsyncEngineArgs(model=path, max_model_len=1440, quantization="awq", block_size=8)
    engine = AsyncLLMEngine.from_engine_args(engine_args)
    print("Starting server...")
    with open('config.json') as f:
        config = json.load(f)
    host = config['llm-server']['host']
    port = config['llm-server']['port']

    asyncio.run(start_server(host, port))
