#!/usr/bin/env python
import asyncio
from websockets.server import serve
import numpy as np

# Callback executed when websocket server is started
async def onWebsocketServerStartExample(websocketServer):
    async for message in websocketServer:
        # Process income websocket message from web page
        print("Message type:", type(message))
        if(isinstance(message, (bytes, bytearray))):
            # binary data
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