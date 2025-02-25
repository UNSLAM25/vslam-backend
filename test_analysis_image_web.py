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
import cv2 as cv

print("Process id:", os.getpid())

# Some arguments from run_video_slam.cc
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--image", help="image file path", default="./files/Teclado Logitech C720 640x480.jpeg")
parser.add_argument("-v", "--vocab", help="vocabulary file path", default="./vslam/orb_vocab.fbow")
parser.add_argument("-c", "--config", help="config file path", default="./vslam/config.yaml")
parser.add_argument("-l", "--map_load", help="load a map")
parser.add_argument("-s", "--map_save", help="save a map after shutdown")
parser.add_argument("-f", "--factor", help="scale factor to show video in window - doesn't affect stella_vslam", default=0.5, type=float)
args = parser.parse_args()

im = cv.imread(args.image)

keypointsProps = ['x', 'y', 'octave', 'angle', 'size', 'response', 'class_id']
keypointsPropsText = ', '.join(keypointsProps)

# Callback executed when websocket server is started
countToPrint = 0
async def onWebsocket(websocketConnection):
    global countToPrint

    # This loop ends when connection is closed
    async for message in websocketConnection:
        # Process income websocket message from web page
        # Each message can be str or bytes
        print(f'message length {len(message)}')
        if(isinstance(message, (bytes, bytearray))): #bytes)):#
            # binary data

            # Is it an image?
            # TODO
            if(len(message) > 500000):
                # Image RGBA 640x480
                messageType = 'color image'
                image = np.frombuffer(message, dtype=np.uint8).reshape(-1, 640, 4)
                image = cv.cvtColor(image, cv.COLOR_RGBA2BGR)
                print(f'Image shape {image.shape}')
                mat = image
                cv.imshow('Image', image)


            elif(len(message) > 300000):
                # Image 640x480
                messageType = 'gray image'
                image = np.frombuffer(message, dtype=np.uint8).reshape(-1, 640)
                print(f'Image shape {image.shape}')
                mat = image
                cv.imshow('Image', image)

            else:        
                # Descriptor, no image
                # 38 columns char array: 32 for descriptor, 6 for compressed keypoint.
                messageType = 'image descriptor'
                imageDescriptor = np.frombuffer(message, dtype=np.uint8).reshape(-1, 38)
                mat = imageDescriptor
                if imageDescriptor[-1, -1] == 255: # last row is debug row
                    # print("shape:", imageDescriptor.shape)
                    # print("1st row:", imageDescriptor[0])
                    # print("last value:",imageDescriptor[-1, -1])

                    # check descriptor integrity
                    debugSum = imageDescriptor[-1, :32].view(dtype=np.float32)[4]
                    descriptorSum = np.sum(imageDescriptor[0, :32])
                    mat = imageDescriptor[:-1, :]
                    if(debugSum != descriptorSum):
                        print("Error: las sumas de descriptores difieren (descriptor y debug): ", descriptorSum, debugSum)
                        print("message: tipo", type(message), "longitud", len(message))
                        print("descriptor dañado:", imageDescriptor[0, :32])


            # VSLAM         
            # Timestamp is important, see: https://github.com/stella-cv/stella_vslam_examples/blob/3606f68c9c3fb05a838e992230cb4a17106a7c41/src/run_camera_slam.cc#L174
            timestamp = time.time()            
            print("Timestamp: ", timestamp)
            retVal, pose = vslamSystem.feed_monocular_frame(mat, timestamp)

            if retVal:
                print("Pose", pose)
            else:
                print("No pose")

            frame_observation = vslamSystem.get_frame_observation()
            descriptors = frame_observation.descriptors
            print(f"Descriptors: {descriptors.shape}")
            kps = frame_observation.undist_keypts
            print(f"Keypoints: {len(kps)}")

            keypoints = [cv.KeyPoint(kp.x, kp.y, kp.size, kp.angle, kp.response, kp.octave, kp.class_id) for kp in kps]
            keypointsText = '\n'.join(['; '.join([str(getattr(kp, prop)).replace('.', ',') for prop in keypointsProps]) for kp in kps])
            #print(keypointsPropsText)
            #print(keypointsText)

            # Save file
            with open('files/keypoints ' + messageType + str(timestamp) + '.csv', "w") as file:
                file.write(keypointsPropsText)
                file.write('\n')
                file.write(keypointsText)

            with open('files/descriptors ' + messageType + str(timestamp) + '.csv', "w") as file:
                file.write('\n'.join(['; '.join([str(element) for element in descriptor]) for descriptor in descriptors]))


            im2 = im.copy()
            cv.drawKeypoints(im, keypoints, im2, (0,255,0))
            cv.imshow('Keypoints', im2)
            key = cv.waitKey(100)

        else:
            # text data
            print("Text:")
            print(message)

            # Are we expecting a JSON?


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
print("http://", get_my_ip_address(), ":", httpPort, "/analysis.html", sep='')
print("You should consider adding this url to chrome://flags/#unsafely-treat-insecure-origin-as-secure")
print("Ctrl+c to stop servers")

# Create a separate thread for serving http
http_thread = Thread(target=runHttpServer, args=(httpPort,))
http_thread.start()

# Create a separate thread for websockets server
ws_thread = Thread(target=runWebsocketServer, kwargs={'port':wsPort, 'onWebsocket': onWebsocket, 'max_size': 1048576*4})
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