'''
Http and websocket servers plus vslam bindings with pangolin viewer
Base code from httpAndWebsocketsServerExample.py
and camTest.py
'''

import stellavslam
import cv2 as cv
import numpy as np
import argparse
from threading import Thread
from websocketServerExample import runWebsocketServer
from httpServer import runHttpServer
from getMyIP import get_my_ip_address
import os

# Callback executed when websocket server is started
async def onWebsocket(websocketServer):
    async for message in websocketServer:
        # Process income websocket message from web page
        print("Message type:", type(message))
        if(isinstance(message, (bytes, bytearray))):
            # binary data
            print("Binary:")

            features = np.frombuffer(message, dtype=np.float32).reshape(-1, 4)
            print("shape:", features.shape, len(features))
            print("keypoint:", features[int(2*len(features)/3)])

            retVal, pose = SLAM.feed_monocular_frame(features, 0.0) # fake timestamp to keep it simple



        else:
            # text data
            print("Text:")
            print(message)

            # Are we expecting a JSON?


# Some arguments from run_video_slam.cc
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--vocab", help="vocabulary file path", default="./orb_vocab.fbow")
parser.add_argument("-m", "--video", help="video file path", default="0")
parser.add_argument("-c", "--config", help="config file path", default="./config_Logitech_c270.yaml")
parser.add_argument("-p", "--map_db", help="store a map database at this path after SLAM")
parser.add_argument("-f", "--factor", help="scale factor to show video in window - doesn't affect stella_vslam", default=0.5, type=float)
args = parser.parse_args()

frameShowFactor = args.factor
config = stellavslam.config(config_file_path=args.config)
SLAM = stellavslam.system(cfg=config, vocab_file_path=args.vocab)
VIEWER = stellavslam.viewer(config, SLAM)
SLAM.startup()
print("stellavslam up and operational.")

httpPort = 8000
wsPort = 8765

print("Connect to this web server through:")
print("http://", get_my_ip_address(), ":", httpPort, "/index.html", sep='')
print("http://", get_my_ip_address(), ":", httpPort, "/test.html", sep='')
print("You should consider adding this url to chrome://flags/#unsafely-treat-insecure-origin-as-secure")
print("Ctrl+c to stop servers")

# Create a separate thread for serving http
http_thread = Thread(target=runHttpServer, args=(httpPort,))
http_thread.start()

# Create a separate thread for websockets server
ws_thread = Thread(target=runWebsocketServer, kwargs={'port':wsPort, 'onWebsocket': onWebsocket})
ws_thread.start()

# Blocking call
VIEWER.run()

# The user pressed Terminate button
SLAM.shutdown()
#http_thread.join()
#ws_thread.join()
print("Finished")
os._exit(0)
