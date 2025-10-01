from argparse import Namespace
from threading import Thread
from lib import stella_vslam as vslam
from websocket import create_websocket_thread

VSLAM_SYSTEM = None 
VSLAM_VIEWER = None

def start_slam(args: Namespace):
    try: 
        global VSLAM_SYSTEM
        global VSLAM_VIEWER
        # frameShowFactor = args.factor
        mapPath = args.map_load
        mapSave = args.map_save
        config = vslam.config(config_file_path=args.config)
        VSLAM_SYSTEM = vslam.system(cfg=config, vocab_file_path=args.vocab)
        VSLAM_VIEWER = vslam.viewer(config.yaml_node_['Viewer'], VSLAM_SYSTEM)

        if mapPath:
            VSLAM_SYSTEM.load_map_database(mapPath)

        VSLAM_SYSTEM.startup()
        
        # run viewer in new thread to prevent GIL blocking
        # viewerThread = Thread(target=run_viewer)
        # viewerThread.start()    

        # Blocking call
        VSLAM_VIEWER.run()

        # The user pressed Terminate button
        VSLAM_SYSTEM.shutdown()

        if (mapSave):
            VSLAM_SYSTEM.save_map_database(mapSave)
    except Exception as error:
        print(error) 

# def run_viewer():
#     global VSLAM_VIEWER
#     VSLAM_VIEWER.run()