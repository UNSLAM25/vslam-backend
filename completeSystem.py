'''
Http and websocket servers plus vslam bindings with pangolin viewer
Base code from httpAndWebsocketsServerExample.py
and camTest.py
'''

from lib import stella_vslam as vslam
import numpy as np
import argparse
from threading import Thread
from lib.websocketServer import runWebsocketServer
from lib.getMyIP import get_my_ip_address
from lib.httpServer import runHttpServer
import os
import time
import json

print("Process id:", os.getpid())

# Some arguments from run_video_slam.cc
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--vocab", help="vocabulary file path", default="./vslam/orb_vocab.fbow")
parser.add_argument("-c", "--config", help="config file path", default="./vslam/config.yaml")
parser.add_argument("-l", "--map_load", help="load a map")
parser.add_argument("-s", "--map_save", help="save a map after shutdown")
parser.add_argument("-f", "--factor", help="scale factor to show video in window - doesn't affect stella_vslam", default=0.5, type=float)
args = parser.parse_args()

# Callback executed when websocket server is started
countToPrint = 0
async def onWebsocket(websocketServer):
    global countToPrint
    descriptorTimestamp = 0
    async for message in websocketServer:
        # Process income websocket message from web page
        if(isinstance(message, (bytes, bytearray))):
            # binary data

            # 38 columns char array: 32 for descriptor, 6 for compressed keypoint.
            imageDescriptor = np.frombuffer(message, dtype=np.uint8).reshape(-1, 38)
            if imageDescriptor[-1, -1] == 255: # last row is debug row
                # check descriptor integrity
                debugSum = imageDescriptor[-1, :32].view(dtype=np.float32)[4]
                descriptorSum = np.sum(imageDescriptor[0, :32])
                if(debugSum != descriptorSum):
                    print("Error: las sumas de descriptores difieren (descriptor y debug): ", descriptorSum, debugSum)
                    print("message: tipo", type(message), "longitud", len(message))
                    print("descriptor dañado:", imageDescriptor[0, :32])
            
            # Debug row
            # myFloatView = imageDescriptor[-1, :32].view(np.float32)
            # for i in range(5):
            #     print(i, myFloatView[i])

            # VSLAM         
            # Timestamp is important, see: https://github.com/stella-cv/stella_vslam_examples/blob/3606f68c9c3fb05a838e992230cb4a17106a7c41/src/run_camera_slam.cc#L174    
            timestamp = 0
            if (descriptorTimestamp == 0):
                print("Descriptor timestamp was not sent, defaulting to system time")
                timestamp = time.time()
            else: 
                timestamp = descriptorTimestamp
                descriptorTimestamp = 0
 
            print("Timestamp: ", timestamp)            
            retVal, pose = vslamSystem.feed_monocular_frame(imageDescriptor[:-1, :], timestamp)
            
            if retVal:
                print("Pose", pose)
                poseMessage = {
                    "type": "pose",
                    "timestamp": time.time(),
                    "status": "ok",
                    "Twc": pose.tolist()
                }
                await websocketServer.send(json.dumps(poseMessage))
            else:
                print("No pose")
        else:
            # text data
            print("Received non-binary data, raw message:", message)            
            try:
                data = json.loads(message)                
                if data['type'] == 'descriptor':
                    descriptorTimestamp = data['timestamp']
                
            except Exception as e:
                print(e)
                print("Data could not be parsed as JSON")
                

frameShowFactor = args.factor
config = vslam.config(config_file_path=args.config)
vslamSystem = vslam.system(cfg=config, vocab_file_path=args.vocab)
vslamViewer = vslam.viewer(config.yaml_node_['Viewer'], vslamSystem)
mapPath = args.map_load
if mapPath:
    vslamSystem.load_map_database(mapPath)

vslamSystem.startup()
print("stellavslam up and operational.")

httpPort = 8000
wsPort = 8765

print("Connect to this web server through:")
print("http://", get_my_ip_address(), ":", httpPort, "/web/index.html", sep='')
print("You should consider adding this url to chrome://flags/#unsafely-treat-insecure-origin-as-secure")
print("Ctrl+c to stop servers")

# Create a separate thread for serving http
http_thread = Thread(target=runHttpServer, args=(httpPort,))
http_thread.start()

# Create a separate thread for websockets server
ws_thread = Thread(target=runWebsocketServer, kwargs={'port':wsPort, 'onWebsocket': onWebsocket})
ws_thread.start()

# Blocking call
vslamViewer.run()

# The user pressed Terminate button
vslamSystem.shutdown()
mapSave = args.map_save
if(mapSave):
    vslamSystem.save_map_database(mapSave)
        
print("Finished")
# It would be nice to kindly ask threads to join instead of abruptly closing them by exiting
os._exit(0)
