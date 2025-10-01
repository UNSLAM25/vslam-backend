
from lib.websocketServer import runWebsocketServer
import time
import json
from threading import Thread
import numpy as np
import slam 

WS_PORT = 8765

# Create a separate thread for websockets server
def create_websocket_thread():
    ws_thread = Thread(target=runWebsocketServer, kwargs={'port': WS_PORT, 'onWebsocket': websocketCallback})
    ws_thread.start()


# Callback executed when websocket server receives messages
async def websocketCallback(websocketServer):  
    descriptorTimestamp = 0 

    async for message in websocketServer:       
        # Process income websocket message from web page
        if(isinstance(message, (bytes, bytearray))):
            # binary data

            # 38 columns char array: 32 for descriptor, 6 for compressed keypoint.
            imageDescriptor = np.frombuffer(message, dtype=np.uint8).reshape(-1, 38)
            handle_checksum(imageDescriptor)
    
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
            retVal, pose = slam.VSLAM_SYSTEM.feed_monocular_frame(imageDescriptor[:-1, :], timestamp)
            
            if retVal:
                poseMessage = {
                    "type": "pose",
                    "timestamp": time.time(),
                    "status": "ok",
                    "Twc": pose.tolist()
                    # pose2D: [x, y, alpha]
                }
                await websocketServer.send(json.dumps(poseMessage))                
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
          

def handle_checksum(imageDescriptor):
    if imageDescriptor[-1, -1] == 255: # last row is debug row     
        debugSum = imageDescriptor[-1, :32].view(dtype=np.float32)[4]
        descriptorSum = np.sum(imageDescriptor[0, :32])
        if debugSum != descriptorSum:
            print("Error: las sumas de descriptores difieren (descriptor y debug): ", descriptorSum, debugSum)
            print("descriptor dañado:", imageDescriptor[0, :32]) 

