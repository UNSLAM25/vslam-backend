'''
This test runs stella_vslam on video.
It only shows the pose matrix and the video feed.
It doesn't show map nor features.

Command line example:
python3 camTtest.py

Valid pose only after initialization.
You can check the pose is valid when last row is 0,0,0,1 .

stella_vslam is not bug free.  Sometimes it crashes (segmentation fault) right after map initialization.
It's not a bindings bug.  Try again - many times - until succeeding.

Map save not tested.
'''
import lib.stellavslam as vslam
import cv2 as cv
import sys
import argparse
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

def run_slam():
    global frameShowFactor
    global video
    global SLAM

    pose = []
    timestamp = 0.0
    print("Entering the video feed loop.")
    print("You should soon see the video in a window, and the 4x4 pose matrix on this terminal.")
    print("ESC to quit (focus on window: click on feeding frame window, then press ESC).")
    is_not_end = True   

    while(is_not_end):
        is_not_end, frame = video.read()
        if(frame.size):
            retVal, pose = SLAM.feed_monocular_frame(frame, timestamp) # fake timestamp to keep it simple
        if((timestamp % 30) == 0):
            print("Timestamp:", timestamp, "shape:", frame.shape, ", Pose:")
            
            # Format pose matrix with only a few decimals
            for row in pose:
                for data in row:
                    sys.stdout.write('{:9.1f}'.format(data))
                print()
        timestamp += 1.0
        key = cv.waitKey(1)  # Needed to refresh imshow window
        if key == -1:
            continue
        elif key == 27:
            # ESC, finish
            break
        key = chr(key).lower()
        if key == 's':
            # save map
            SLAM.save_map_database(mapPath)
            print("Map saved!", mapPath)
            continue


SLAM = vslam.system(cfg=config, vocab_file_path=args.vocab)
VIEWER = vslam.viewer(config, SLAM)

mapPath = args.map_db
if mapPath:
    SLAM.load_map_database(mapPath)

SLAM.startup()
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

slamThreadInstance = Thread(target=run_slam)
slamThreadInstance.start()
VIEWER.run()
slamThreadInstance.join()
SLAM.shutdown()