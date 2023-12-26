'''
Http and websocket servers plus vslam bindings with pangolin viewer
Base code from httpAndWebsocketsServerExample.py
and camTest.py
'''

#import sys
#sys.path.append("lib")
import lib.stellavslam as vslam
import numpy as np
import cv2 as cv
import argparse
from threading import Thread
from lib.websocketServer import runWebsocketServer
from lib.getMyIP import get_my_ip_address
from lib.httpServer import runHttpServer
import os
import sys

print("Process id:", os.getpid())

# Some arguments from run_video_slam.cc
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--vocab", help="vocabulary file path", default="./vslam/orb_vocab.fbow")
parser.add_argument("-m", "--video", help="video file path", default="")
parser.add_argument("-c", "--config", help="config file path", default="./vslam/config Logitech c270 640x480 calibrado.yaml")
parser.add_argument("-p", "--map_db", help="store a map database at this path after SLAM")
parser.add_argument("-f", "--factor", help="scale factor to show video in window - doesn't affect stella_vslam", default=0.5, type=float)
parser.add_argument("-l", "--local", help="local webcam", default="")

args = parser.parse_args()
config = vslam.config(config_file_path=args.config)
frameShowFactor = args.factor


# Callback executed when websocket server is started
countToPrint = 0
timestamp = 0.0

async def onWebsocket(websocketServer):
    global countToPrint
    global timestamp
    
    async for message in websocketServer:
        # Process income websocket message from web page
        if(isinstance(message, bytes)):
            # binary data

            size = len(message)
            print("Message len:", size)

            if not(size % 38):
                # Image descriptor
                print("Image descriptor:")

                # 38 columns char array: 32 for descriptor, 6 for compressed keypoint.
                imageDescriptor = np.frombuffer(message, dtype=np.uint8).reshape(-1, 38)
                if imageDescriptor[-1, -1] == 255: # last row is debug row
                    print("shape:", imageDescriptor.shape)
                    print("1st row:", imageDescriptor[0])
                    print("last value:",imageDescriptor[-1, -1])

                    # check descriptor integrity
                    debugSum = imageDescriptor[-1, :32].view(dtype=np.float32)[4]
                    descriptorSum = np.sum(imageDescriptor[0, :32])
                    if(debugSum != descriptorSum):
                        print("Error: las sumas de descriptores difieren (descriptor y debug): ", descriptorSum, debugSum)
                        print("message: tipo", type(message), "longitud", len(message))
                        print("descriptor dañado:", imageDescriptor[0, :32])
                    else:
                        # no error
                        countToPrint = (countToPrint + 1) % 10
                        if(countToPrint == 0):
                            print("descriptor sano:", imageDescriptor[0, :32])

                # Print first keypoint
                myShortView = imageDescriptor.view(np.uint16)
                print("x,y,angle", myShortView[0,16], myShortView[0,17], 360.0 / 255.0 * imageDescriptor[0,36])

                # Debug row
                myFloatView = imageDescriptor[-1, 0:32].view(np.float32)
                for i in range(5):
                    print(i, myFloatView[i])

                image = imageDescriptor # for vslam feeding
                
            else:
                # Image
                print("Image from web page:")
                image = np.frombuffer(message, dtype=np.uint8).reshape(480, 640, 4) # RGBA
                image = cv.cvtColor(image, cv.COLOR_RGBA2BGR)
                print("shape:", image.shape)

            # VSLAM
            retVal, pose = SLAM.feed_monocular_frame(image, timestamp)
            if retVal:
                print("Pose", pose)
            else:
                print("No pose")

            timestamp += 1.0

            if((timestamp % 30) == 0):
                print("Timestamp:", timestamp, "shape:", image.shape, ", Pose:")
        
                # Format pose matrix with only a few decimals
                for row in pose:
                    for data in row:
                        sys.stdout.write('{:9.1f}'.format(data))
                        print()
    



        elif (isinstance(message, str)):
            # text data
            print("Text:")
            print(message)

            # Are we expecting a JSON?

        else:
            print("Another type")
            print(message)
            print("Type:", type(message))
            #print(isinstance(message, ImageData))


def runLocalVSlam():
    global timestamp
    while True:
        ret, im = webcam.read()
        # VSLAM
        retVal, pose = SLAM.feed_monocular_frame(im, timestamp)
        if retVal:
            print("Pose", pose)
        else:
            print("No pose")

        timestamp += 1.0        
        cv.waitKey(30)


SLAM = vslam.system(cfg=config, vocab_file_path=args.vocab)
VIEWER = vslam.viewer(config, SLAM)
mapPath = args.map_db
if mapPath:
    SLAM.load_map_database(mapPath)

SLAM.startup()
print("stellavslam up and operational.")


httpPort = 8000
wsPort = 8765

print("Connect to this web server through:")
print("http://", get_my_ip_address(), ":", httpPort, "/index.html", sep='')
print("You should consider adding this url to chrome://flags/#unsafely-treat-insecure-origin-as-secure")
print("Ctrl+c to stop servers")

# Create a separate thread for serving http
http_thread = Thread(target=runHttpServer, args=(httpPort,))
http_thread.start()

# Create a separate thread for websockets server
ws_thread = Thread(target=runWebsocketServer, kwargs={'port':wsPort, 'onWebsocket': onWebsocket, 'max_size': 10000000})
ws_thread.start()

webcam = 0
if args.local:
    webcam = cv.VideoCapture(0)
    webcam.set(cv.CAP_PROP_FRAME_WIDTH, 640)
    webcam.set(cv.CAP_PROP_FRAME_HEIGHT, 480)

    local_thread = Thread(target=runLocalVSlam)
    local_thread.start()

# Blocking call
VIEWER.run()

# The user pressed Terminate button
SLAM.shutdown()
print("Finished")
# It would be nice to kindly ask threads to join instead of abruptly closing them by exiting
os._exit(0)
