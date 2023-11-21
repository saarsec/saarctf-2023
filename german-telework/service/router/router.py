from socketserver import ThreadingTCPServer,StreamRequestHandler
import socket

import transport_crypt

# TODO: fix java encoding and decoding here instead of gateway

def utf8s_to_utf8m(string):
    """
    :param string: utf8 encoded string 
    :return: modified utf8 encoded string
    """
    new_str = []
    i = 0
    while i < len(string):
        byte1 = string[i]
        # NULL bytes and bytes starting with 11110xxx are special
        if (byte1 & 0x80) == 0:
            if byte1 == 0:
                new_str.append(0xC0)
                new_str.append(0x80)
            else:
                # Single byte
                new_str.append(byte1)

        elif (byte1 & 0xE0) == 0xC0:  # 2byte encoding
            new_str.append(byte1)
            i += 1
            new_str.append(string[i])

        elif (byte1 & 0xF0) == 0xE0:  # 3byte encoding
            new_str.append(byte1)
            i += 1
            new_str.append(string[i])
            i += 1
            new_str.append(string[i])

        elif (byte1 & 0xF8) == 0xF0:  # 4byte encoding
            # Beginning of 4byte encoding, turn into 2 3byte encodings
            # Bits in: 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
            i += 1
            byte2 = string[i]
            i += 1
            byte3 = string[i]
            i += 1
            byte4 = string[i]

            # Reconstruct full 21bit value
            u21 = (byte1 & 0x07) << 18
            u21 += (byte2 & 0x3F) << 12
            u21 += (byte3 & 0x3F) << 6
            u21 += (byte4 & 0x3F)

            # Bits out: 11101101 1010xxxx 10xxxxxx
            new_str.append(0xED)
            new_str.append((0xA0 + (((u21 >> 16) - 1) & 0x0F)))
            new_str.append((0x80 + ((u21 >> 10) & 0x3F)))

            # Bits out: 11101101 1011xxxx 10xxxxxx
            new_str.append(0xED)
            new_str.append((0xB0 + ((u21 >> 6) & 0x0F)))
            new_str.append(byte4)
        i += 1
    return bytes(new_str)


def utf8m_to_utf8s(string):
    """
    :param string: modified utf8 encoded string 
    :return: utf8 encoded string
    """
    new_string = []
    length = len(string)
    i = 0
    while i < length:
        byte1 = string[i]
        if (byte1 & 0x80) == 0:  # 1byte encoding
            new_string.append(byte1)
        elif (byte1 & 0xE0) == 0xC0:  # 2byte encoding
            i += 1
            byte2 = string[i]
            if byte1 != 0xC0 or byte2 != 0x80:
                new_string.append(byte1)
                new_string.append(byte2)
            else:
                new_string.append(0)
        elif (byte1 & 0xF0) == 0xE0:  # 3byte encoding
            i += 1
            byte2 = string[i]
            i += 1
            byte3 = string[i]
            if i+3 < length and byte1 == 0xED and (byte2 & 0xF0) == 0xA0:
                # See if this is a pair of 3byte encodings
                byte4 = string[i+1]
                byte5 = string[i+2]
                byte6 = string[i+3]
                if byte4 == 0xED and (byte5 & 0xF0) == 0xB0:
                    
                    # Bits in: 11101101 1010xxxx 10xxxxxx
                    # Bits in: 11101101 1011xxxx 10xxxxxx
                    i += 3
                    
                    # Reconstruct 21 bit code
                    u21 = ((byte2 & 0x0F) + 1) << 16
                    u21 += (byte3 & 0x3F) << 10
                    u21 += (byte5 & 0x0F) << 6
                    u21 += (byte6 & 0x3F)
                    
                    # Bits out: 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
                    
                    # Convert to 4byte encoding
                    new_string.append(0xF0 + ((u21 >> 18) & 0x07))
                    new_string.append(0x80 + ((u21 >> 12) & 0x3F))
                    new_string.append(0x80 + ((u21 >> 6) & 0x3F))
                    new_string.append(0x80 + (u21 & 0x3F))
                    continue 
            new_string.append(byte1)
            new_string.append(byte2)
            new_string.append(byte3)
        i += 1
    return bytes(new_string)




# TODO: move to config
HOST = "127.0.0.1"
IN_PORT = 30001
TIMEOUT = 5
services = {
    # the task backend
    "0" : 30002,
    # the leave request backend
    "1" : 30003,
    # the messagecrypt backend
    "2" : 30005,
    # the board backend
    "3" : 30007,
    # the gateway port
    "4" : 30000
}


class Echohandler(StreamRequestHandler):
    
    timeout = TIMEOUT 
    
    def handle(self):
        print(f'Connected: {self.client_address[0]}:{self.client_address[1]}')
        data = self.request.recv(1024)
        data = transport_crypt.transport_crypt(bytearray(data))
        data = data.strip(b"\n").decode("utf-8")
        print(f"received: {data}")
        try:
            reply = forward(data)
            reply = reply.encode("utf-8")
            reply = transport_crypt.transport_crypt(bytearray(reply))
            self.request.send(reply)
        except TimeoutError:
           print("Timeout, exiting...")
        except ConnectionRefusedError: 
           print("Target is not reachable")


def get_target(data):
    print(f"Forwarding network packet {data}")
    parts = data.split("|||")
    target = services[parts[0]]
    return target


def forward(data):
    dest_port = get_target(data)
    print("Destination:",dest_port)
    target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    target.connect((HOST, dest_port))
    data = data + '\n'
    # if dest_port == 30002:
    #     target.send(encode_modified_utf8(data))
    # else:
    #     target.send(data.encode("utf-8"))
    data = data.encode("utf-8")
    data = transport_crypt.transport_crypt(bytearray(data))
    target.send(data)
    print("Waiting for data from ", target)
    tc_state_recv = transport_crypt.TransportCryptState()
    buffer = b""
    char = b""
    while bytes(char) != b"\n":
        char = target.recv(1)
        if len(char) == 0:
            break
        char = tc_state_recv.transport_crypt(bytearray(char))
        buffer += char
    target.close()
    decoded_reply = ""
    print(f"Full reply: {buffer}")
    #if dest_port == 30002:
    #    print("Decoding task stuff!")
    #    decoded_reply = utf8m_to_utf8s(buffer)
    #    decoded_reply = decoded_reply.decode("utf-8")
    #else:
    print("Decoding generic utf8!")
    decoded_reply = buffer.decode("utf-8")
    print(f"Decoded: {decoded_reply}")
    return decoded_reply 


if __name__ == "__main__":
    ThreadingTCPServer.allow_reuse_address = True
    server = ThreadingTCPServer((HOST,IN_PORT),Echohandler)
    server.serve_forever()
