# http server
# run as main, or import and use runHttpServer(port)

import http.server

httpPort = 8000

# Webserver
class SimpleHTTPRequestHandlerWithCORS (http.server.SimpleHTTPRequestHandler):
    def end_headers (self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        super().end_headers()

SimpleHTTPRequestHandlerWithCORS.extensions_map['.wasm'] = 'application/wasm'

# Create a server on this IP with the given port
def createHttpServer(httpPort=8000):
    return http.server.ThreadingHTTPServer(("", httpPort), SimpleHTTPRequestHandlerWithCORS)

# Run a provided server, or create it from a port and run
def runHttpServer(serverOrPort=8000):
    if isinstance(serverOrPort,(int,float)):
        # server is a port number, let's create a proper server
        server = createHttpServer(serverOrPort)
    else:
        server = serverOrPort
        
    server.serve_forever()

async def runAsyncHttpServer(serverOrPort=8000):
    await runHttpServer(serverOrPort)

# Launch server if main
if __name__ == "__main__":
    from getMyIP import get_my_ip_address
    print("Connect to this web server through:")
    print("http://", get_my_ip_address(), ":", httpPort, "/index.html", sep='')
    print("You should consider adding this url to chrome://flags/#unsafely-treat-insecure-origin-as-secure")
    print("Ctrl+c to stop servers")

    runHttpServer()