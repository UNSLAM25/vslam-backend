# Get this server IP address
import socket

def get_my_ip_address(test="8.8.8.8"):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    myIP = ""
    try:
        sock.connect((test, 80))
        myIP = sock.getsockname()[0]
    finally:
        sock.close()
        return myIP
