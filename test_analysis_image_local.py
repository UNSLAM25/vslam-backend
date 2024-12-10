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

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--image", help="image file path", default="./files/Teclado Logitech C720 640x480.jpeg")
parser.add_argument("-v", "--vocab", help="vocabulary file path", default="./vslam/orb_vocab.fbow")
parser.add_argument("-c", "--config", help="config file path", default="./vslam/config.yaml")
parser.add_argument("-f", "--factor", help="scale factor to show video in window - doesn't affect stella_vslam", default=0.5, type=float)
args = parser.parse_args()
config = vslam.config(config_file_path=args.config)


keypointsProps = ['x', 'y', 'octave', 'angle', 'size', 'response', 'class_id']
keypointsPropsText = ', '.join(keypointsProps)

def convert_to_cv2_keypoints(kps):
    return [cv.KeyPoint(kp.x, kp.y, kp.size, kp.angle, kp.response, kp.octave, kp.class_id) for kp in kps]


im = cv.imread(args.image)

vslamSystem = vslam.system(cfg=config, vocab_file_path=args.vocab)
vslamSystem.startup()
print("stellavslam up and operational.")

retVal, pose = vslamSystem.feed_monocular_frame(im, 0.0) # fake timestamp to keep it simple
frame_observation = vslamSystem.get_frame_observation()
print(f"Descriptors: {frame_observation.descriptors.shape}")
kps = frame_observation.undist_keypts
print(f"Keypoints: {len(kps)}")

keypoints = [cv.KeyPoint(kp.x, kp.y, kp.size, kp.angle, kp.response, kp.octave, kp.class_id) for kp in kps]
keypointsText = '\n'.join([', '.join([str(getattr(kp, prop)) for prop in keypointsProps]) for kp in kps])
print(keypointsPropsText)
print(keypointsText)

cv.drawKeypoints(im, convert_to_cv2_keypoints(kps), im, (0,255,0))
cv.imshow('Image', im)
key = cv.waitKey(0)

vslamSystem.shutdown()