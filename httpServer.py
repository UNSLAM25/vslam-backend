from threading import Thread
from lib.httpServer import runHttpServer
from lib.getMyIP import get_my_ip_address

HTTP_PORT = 8000

# Create a separate thread for serving http
def create_http_server_thread():
    http_thread = Thread(target=runHttpServer, args=(HTTP_PORT,))
    http_thread.start()
    
    print("HTTP Server started.")
    print("Connect to this web server through:")
    print("http://", get_my_ip_address(), ":", HTTP_PORT, "/web/index.html", sep='')
    print("You should consider adding this url to chrome://flags/#unsafely-treat-insecure-origin-as-secure")
    print("Ctrl+c to stop servers")
