import socket
import select
import sys
from _thread import *

if len(sys.argv) > 1:
    SERVER_PORT = int(sys.argv[2])
else:
    SERVER_PORT = 8001

MAX_CONNECTION = 5 # set number of connection
HOST = ''
BUFFER_SIZE = 2048 # set buffer size


def main():
    num = 0
    try: # server initialization
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # sever socket
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((HOST, SERVER_PORT)) # sever bind
        server_sock.listen(MAX_CONNECTION) # sever listen
        print("server started at [%d]" %(SERVER_PORT))
    except Exception: # if port is alreay using or another execption
        print("Address already in use")
        print(Exception)
        server_sock.close()
        sys.exit(1)

    while True:
        try:
            num+=1
            client_sock, addr = server_sock.accept() # client socket
            read_bytes = client_sock.recv(BUFFER_SIZE)
            print('Request: %d\n' %num)
            start_new_thread(parsing_request, (client_sock, read_bytes, num))

        except KeyboardInterrupt:
            server_sock.close()
            print("EXIT")
            sys.exit(1)


# parsing and Request
def parsing_request(client_sock, read_bytes, num):
    headers = read_bytes.split('\n')[0]
    url_pos = headers.find("http")
    url = read_bytes[url_pos:]

    method = read_bytes[:url_pos-1]
    if method != "GET": # if method is not GET
        http_pos = url.find("HTTP")
        resp = url[http_pos:] + "501 Not Implemented\n"
        client_sock.send(resp)
        print("Response Done: %d" %num)
        print(resp.split('\n')[0])
        client_sock.close()
    else :
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
        conn_pos = read_bytes.find("\r\nConnection:")
        # if conn_pos == -1:
        #     host_pos = read_bytes.find("Host:")
        #     read_bytes = read_bytes[:host_pos] + "Connection: close\r\n" + read_bytes[host_pos:]
        # else: 
        #     conn_ePos = read_bytes.find("\r\n", conn_pos)
        #     if conn_ePos == -1:
        #         read_bytes = read_bytes
        #     else:
        #         read_bytes = read_bytes[:conn_pos] + "\r\nConnection: close" + read_bytes[conn_ePos:]

        url = url.replace('/','_') # for cache file name
        isCached = check_cache(url) 
        print(read_bytes)
        if isCached:
            print("HIT") # it exists in the cache.
            client_sock.send(isCached)
            print("Response Done: %d" %num)
            print(isCached.split('\n')[0])
            client_sock.close()
        else:
            print("MISS") # it isn't
            request_server(url, domain, port, client_sock, read_bytes, num)
            client_sock.close()


# check cached
def check_cache(url):
    try:
        if len(url) > 200:
            url = url[:199]
        cache = open(url) # if file is exists, it exist in the cache
        reply = cache.read()
        cache.close()
        return reply
    except IOError:
        return None


# call server
def request_server(url, domain, port, client_sock, read_bytes, num):
    try:
        oriserver_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        oriserver_sock.connect((domain, port))
        oriserver_sock.send(read_bytes)
        server_read_bytes = ""

        # receive a response as much as the buffer size.
        while 1:
            reply = oriserver_sock.recv(BUFFER_SIZE)

            if(len(reply)>0):
                server_read_bytes += reply
                client_sock.send(reply)
            else:
                break

        # received all the responses from the server.
        save_cache(url, server_read_bytes)
        print("Response Done: %d" %num)
        print(server_read_bytes.split('\n')[0])
        oriserver_sock.close()

    except socket.error:
        oriserver_sock.close()
        client_sock.close()
        sys.exit(1)

# save in the cache
def save_cache(url, server_read_bytes):
    if len(url) > 200:
        url = url[:199]
    cached_file = open(url, 'w')
    cached_file.write(server_read_bytes)
    cached_file.close()
    

main()