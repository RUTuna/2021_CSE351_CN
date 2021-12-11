import socket
import sys
from _thread import *

if len(sys.argv) > 1:
    SERVER_PORT = int(sys.argv[2])
else:
    SERVER_PORT = 8001
MAX_CONNECTION = 1 # set number of connection
BUFFER_SIZE = 1024 # set buffer size


def main():
    try: # server initialization
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # sever socket
        server_sock.bind(('', SERVER_PORT)) # sever bind
        server_sock.listen(MAX_CONNECTION) # sever listen
        print("server started at [%d]" %(SERVER_PORT))
    except Exception: # if port is alreay using or another execption
        print(Exception)
        sys.exit(1)

    while True:
        try:
            client_sock, addr = server_sock.accept() # client socket
            read_bytes = client_sock.recv(BUFFER_SIZE).decode()
            start_new_thread(parsing_request, (client_sock, read_bytes))

        except KeyboardInterrupt:
            server_sock.close()
            print("EXIT")
            sys.exit(1)


# parsing and Request
def parsing_request(client_sock, read_bytes):
    print(read_bytes)
    headers = read_bytes.split('\n')[0]
    url = headers.split(' ')[1]

    # remove protocol
    protocol_pos = url.find(":/") 
    if protocol_pos == -1:
        url = url # it isn't real url
    else:
        url = url[protocol_pos + 3:] # it isn't real url

    # export host and port
    path_pos = url.find("/")
    if path_pos == -1:
        path_pos = len(url)

    port_pos = url.find(":")
    if (port_pos == -1 or path_pos < port_pos): # port num was not given.
        port = 80 # defalut port num
        domain = url[:path_pos]
    else:
        port = int((url[port_pos + 1:])[:path_pos - port_pos - 1])
        domain = url[:port_pos]
    
    # add host
    host_pos = read_bytes.find("Host:")
    if host_pos == -1:
        read_bytes = read_bytes + "Host: " + domain + "\r\n"

    # add or change connection option
    conn_pos = read_bytes.find("Connection:")
    if conn_pos == -1:
        read_bytes = read_bytes + "Connection: close\r\n"
    else: 
        conn_ePos = read_bytes.find("\r\n", conn_pos)
        if conn_ePos == -1:
            read_bytes = read_bytes
        else:
            front = read_bytes[:conn_pos]
            back = read_bytes[conn_ePos:]
            read_bytes = front + "Connection: close" + back

    read_bytes = read_bytes + "\r\n"
    read_bytes = read_bytes.encode()

    url = url.replace('/','_') # for cache file name
    isCached = check_cache(url) 
    if isCached:
        print("HIT") # it exists in the cache.
        isCached = isCached.encode()
        client_sock.send(isCached)
        print("Response Done\n")
        client_sock.close()
    else:
        print("MISS") # it isn't
        request_server(url, domain, port, client_sock, read_bytes)


# check cached
def check_cache(url):
    try:
        cache = open(url) # if file is exists, it exist in the cache
        reply = cache.read()
        cache.close()
        return reply
    except IOError:
        return None


# call server
def request_server(url, domain, port, client_sock, read_bytes):
    try:
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.connect((domain, port))
        server_sock.send(read_bytes)
        server_read_bytes = ""

        # receive a response as much as the buffer size.
        while 1:
            reply = server_sock.recv(BUFFER_SIZE)

            if(len(reply)>0):
                server_read_bytes += reply.decode()
                client_sock.send(reply)
            else:
                break

        # received all the responses from the server.
        save_cache(url, server_read_bytes)
        print("Response Done\n")
        server_sock.close()
        client_sock.close()

    except socket.error:
        server_sock.close()
        client_sock.close()
        sys.exit(1)

# save in the cache
def save_cache(url, server_read_bytes):
    cached_file = open(url, 'w')
    cached_file.write(server_read_bytes)
    cached_file.close()
    

main()