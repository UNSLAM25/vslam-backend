'''
Http and websocket servers plus vslam bindings with pangolin viewer
Base code from httpAndWebsocketsServerExample.py
and camTest.py
'''

from multiprocessing import Process
from httpServer import create_http_server_thread
from lib import stella_vslam as vslam
import argparse
import os

from slam import start_slam
from websocket import create_websocket_thread

def main():
    try: 
        print("Process id:", os.getpid())

        # Some arguments from run_video_slam.cc
        parser = argparse.ArgumentParser()
        parser.add_argument("-v", "--vocab", help="vocabulary file path", default="./vslam/orb_vocab.fbow")
        parser.add_argument("-c", "--config", help="config file path", default="./vslam/config.yaml")
        parser.add_argument("-l", "--map_load", help="load a map")
        parser.add_argument("-s", "--map_save", help="save a map after shutdown")
        parser.add_argument("-f", "--factor", help="scale factor to show video in window - doesn't affect stella_vslam", default=0.5, type=float)
        args = parser.parse_args()


        create_http_server_thread()
        create_websocket_thread()

        start_slam(args)

        os._exit(0)
    except Exception as error:
        print("Exception thrown: ", error)


main()