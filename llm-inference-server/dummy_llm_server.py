import asyncio
import json
import signal

import websockets

from types_and_constants import WS_EOS

CONTENT = """
We're no strangers to love
You know the rules and so do I (do I)
A full commitment's what I'm thinking of
You wouldn't get this from any other guy
I just wanna tell you how I'm feeling
Gotta make you understand

Never gonna give you up
Never gonna let you down
Never gonna run around and desert you
Never gonna make you cry
Never gonna say goodbye
Never gonna tell a lie and hurt you

We've known each other for so long
Your heart's been aching, but you're too shy to say it (say it)
Inside, we both know what's been going on (going on)
We know the game and we're gonna play it
And if you ask me how I'm feeling
Don't tell me you're too blind to see

Never gonna give you up
Never gonna let you down
Never gonna run around and desert you
Never gonna make you cry
Never gonna say goodbye
Never gonna tell a lie and hurt you
Never gonna give you up
Never gonna let you down
Never gonna run around and desert you

Never gonna make you cry
Never gonna say goodbye
Never gonna tell a lie and hurt you
We've known each other for so long
Your heart's been aching, but you're too shy to say it (to say it)
Inside, we both know what's been going on (going on)
We know the game and we're gonna play it
I just wanna tell you how I'm feeling
Gotta make you understand

Never gonna give you up
Never gonna let you down
Never gonna run around and desert you
Never gonna make you cry
Never gonna say goodbye
Never gonna tell a lie and hurt you
"""


async def handle_client(websocket: websockets.WebSocketServerProtocol, path: str = None):
    try:
        while True:
            # Receive a string input from the client
            client_input = await websocket.recv()
            print(f"Received input: {client_input}\n\n")

            last_index = 0
            # Send the input to the model and get the output
            for word in CONTENT.splitlines():
                await websocket.send(word + "\n")
                await asyncio.sleep(0.3)
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
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)
    print("Press Ctrl+C to stop the server")
    print(f"Server Listening on {host}:{port}")

    async with websockets.serve(handle_client, host, port, ping_interval=None):
        await stop


if __name__ == "__main__":
    print("Loading LLM...")

    print("Starting server...")
    with open('config.json') as f:
        config = json.load(f)
    host = config['llm-server']['host']
    port = config['llm-server']['port']

    asyncio.run(start_server(host, port))
