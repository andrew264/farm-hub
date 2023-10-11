import asyncio
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

            # Send the input to the model and get the output
            for token in llm(client_input, stream=True,
                             top_p=0.9, temperature=1.2, batch_size=1,
                             max_new_tokens=512, ):
                await websocket.send(token)

            # send eos
            await websocket.send(WS_EOS)

    except websockets.ConnectionClosedError:
        print("Client disconnected")
    except websockets.ConnectionClosedOK:
        print("Client disconnected")


if __name__ == "__main__":
    print("Loading model...")
    llm = AutoModelForCausalLM.from_pretrained("./Bloke/model.gguf",
                                               model_type="llama",
                                               context_length=4096,
                                               gpu_layers=30, )
    print("Starting server...")

    start_server = websockets.serve(handle_client, "localhost", 8765)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
