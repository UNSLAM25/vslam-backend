import sys
sys.path.append("lib")
from getMyIP import get_my_ip_address
from websocketServer import runWebsocketServer
from httpServer import runHttpServer
from threading import Thread

httpPort = 8000
wsPort = 8765

print("Connect to this web server through:")
print("http://", get_my_ip_address(), ":", httpPort, "/tests/testWebsocket.html", sep='')
print("http://", get_my_ip_address(), ":", httpPort, "/tests/testBuffer.html", sep='')
print("You should consider adding this url to chrome://flags/#unsafely-treat-insecure-origin-as-secure")
print("Ctrl+c to stop servers")

# Create a separate thread for serving http
http_thread = Thread(target=runHttpServer, args=(httpPort,))
http_thread.start()

# Create a separate thread for websockets server
ws_thread = Thread(target=runWebsocketServer, kwargs={'port':wsPort})
ws_thread.start()

http_thread.join()
ws_thread.join()