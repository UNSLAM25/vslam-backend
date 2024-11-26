'''
Analysis binding check.
Based on camTest.py .
Map save not tested.
'''
import lib.stella_vslam as vslam
import cv2 as cv
import sys
import argparse
import os
from threading import Thread

# Some arguments from run_video_slam.cc
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--vocab", help="vocabulary file path", default="./vslam/orb_vocab.fbow")
parser.add_argument("-m", "--video", help="video file path", default="0")
parser.add_argument("-c", "--config", help="config file path", default="./vslam/config.yaml")
parser.add_argument("-p", "--map_db", help="open and store a map database at this path after SLAM")
parser.add_argument("-f", "--factor", help="scale factor to show video in window - doesn't affect stella_vslam", default=0.5, type=float)
args = parser.parse_args()
config = vslam.config(config_file_path=args.config)

def convert_to_cv2_keypoints(kps):
    return [cv.KeyPoint(kp.x, kp.y, kp.size, kp.angle, kp.response, kp.octave, kp.class_id) for kp in kps]

def run_slam():
    global frameShowFactor
    global video
    global vslamSystem

    pose = []
    timestamp = 0.0
    frame_observation = 0
    skipPrintCount = 0
    print("Entering the video feed loop.")
    print("You should soon see the video in a window, and the 4x4 pose matrix on this terminal.")
    print("ESC to quit (focus on window: click on feeding frame window, then press ESC).")
    is_not_end = True

    while(is_not_end):
        is_not_end, frame = video.read()
        if(frame.size):
            retVal, pose = vslamSystem.feed_monocular_frame(frame, timestamp) # fake timestamp to keep it simple
            frame_observation = vslamSystem.get_frame_observation()
        if(skipPrintCount >= 30):
            skipPrintCount = 0
            print(f"Timestamp: {timestamp}, shape: {frame.shape}, retVal: {retVal}")                
            print(f"Descriptors: {frame_observation.descriptors.shape}")
            kps = frame_observation.undist_keypts
            print(f"Keypoints: {len(kps)}")
            print(f"Status: {vslamSystem.get_state()}")
            
            # Format pose matrix with only a few decimals
            if retVal:
                for row in pose:
                    for data in row:
                        sys.stdout.write('{:9.1f}'.format(data))
                    print()

        timestamp += 0.033
        skipPrintCount += 1

        key = cv.waitKey(1)  # Needed to refresh imshow window
        if key == -1:
            continue
        elif key == 27:
            # ESC, finish
            break
        key = chr(key).lower()
        if key == 's':
            # save map
            vslamSystem.save_map_database(mapPath)
            print("Map saved!", mapPath)
            continue


vslamSystem = vslam.system(cfg=config, vocab_file_path=args.vocab)
vslamViewer = vslam.viewer(config.yaml_node_['Viewer'], vslamSystem)

mapPath = args.map_db
if mapPath:
    vslamSystem.load_map_database(mapPath)

vslamSystem.startup()
print("stellavslam up and operational.")

if(args.video.isdigit()):
    # is camera
    args.video = int(args.video)
video = cv.VideoCapture(args.video)

# seteo específico de webcam, hay que quitarlo para otro tipo
video.set(cv.CAP_PROP_FRAME_WIDTH, 640)
video.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
#width = video.get(cv.CAP_PROP_FRAME_WIDTH)
#height = video.get(cv.CAP_PROP_FRAME_HEIGHT)
#print("Resolución:", width, height)

frameShowFactor = args.factor

vslamThreadInstance = Thread(target=run_slam)
vslamThreadInstance.start()
vslamViewer.run()

vslamSystem.shutdown()
print("Finished")
# It should be nicer to kindly ask threads to join instead of abruptly closing them by exiting
os._exit(0)
vslamThreadInstance.join()
