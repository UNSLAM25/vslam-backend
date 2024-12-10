#!/usr/bin/env python
import asyncio
from websockets.server import serve
import numpy as np

# Callback executed when websocket server is started
async def onWebsocketServerStartExample(websocketConnection):
    async for message in websocketConnection:
        # Process income websocket message from web page
        # Each message can be str or bytes
        print("Message type:", type(message))
        if(isinstance(message, (bytes, bytearray))):
            # binary data: bytes are immutable, bytearrays are mutable
            print("Binary:")

            features = np.frombuffer(message, dtype=np.float32).reshape(-1, 4)
            print("shape:", features.shape, len(features))

        else:
            # text data
            print("Text:")
            print(message)

            # Are we expecting a JSON?

# Run websocket server on given port
def runWebsocketServer(onWebsocket=onWebsocketServerStartExample, port=8765, **kwargServe):
    asyncio.run(runAsyncWebsocketServer(onWebsocket, port, **kwargServe))

async def runAsyncWebsocketServer(onWebsocket=onWebsocketServerStartExample, port=8765, **kwargServe):
    print("Websocket server running on port", port)
    async with await serve(onWebsocket, "", port, **kwargServe):
        await asyncio.Future()  # run forever

# Launch server if main
if __name__ == "__main__":
    runWebsocketServer()