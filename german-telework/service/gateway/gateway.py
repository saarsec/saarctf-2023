from socketserver import ThreadingTCPServer,StreamRequestHandler
import socket
import base64
import select
import os
import ssl

import actions.user
import actions.task
import actions.leave
import actions.messagecrypt
import actions.board

import transport_crypt

HOST = "0.0.0.0"
IN_PORT = 30000
ROUTER_PORT = 30001
TIMEOUT = 30 
INTERNAL_TIMEOUT = 5

class Echohandler(StreamRequestHandler):
    
    timeout = TIMEOUT 
    
    def handle(self):
        print(f'Connected: {self.client_address[0]}:{self.client_address[1]}')
        try:
            user_menu(self.request)
        except TimeoutError:
            print("Timeout, exiting...")


def user_menu(s):
    s.send(b"Welcome to German Telework!\n")
    s.send(b"What do you want to do?\n")
    s.send(b"Register\n")
    s.send(b"Login\n")
    s.send(b"Goodbye\n")
    msg = s.recv(1024).strip(b"\n")
    if not msg:
        return
    if msg.lower() == b"register":
        res = register_menu(s)
        if res:
            logged_in_menu(s, res)
        s.close()
        return
    if msg.lower() == b"login":
        res = login_menu(s) 
        if res:
            logged_in_menu(s,res)
        else:
            s.send(b"Error logging in requested user\n")
            s.close()
            return
    if msg.lower() == b"goodbye":
        s.close()
        return


def logged_in_menu(s, user):
    s.send(b"Welcome, " + bytes(user.firstname,"utf-8") + b"\n")
    while True:
        s.send(b"What do you want to do?\n")
        s.send(b"Check my tasks\n")
        s.send(b"Check my holidays\n")
        s.send(b"Encrypt or decrypt a message\n")
        s.send(b"Read or post important announcements\n")
        s.send(b"View the employee register\n")
        msg = s.recv(1024).strip(b"\n")
        if not msg:
            return
        if msg.lower() == b"check my tasks":
            task = actions.task.task_menu(s)
            if task:
                reply = send_to_router(user, task).strip(b"\n")
                user = handle_task_reply(s, reply)
        elif msg.lower() == b"check my holidays":
            holiday = actions.leave.leave_menu(s)
            if holiday:
                reply = send_to_router(user, holiday).strip(b"\n")
                tmp = handle_leave_reply(s, reply)
                if tmp:
                    user = tmp
        elif msg.lower() == b"encrypt or decrypt a message":
            message = actions.messagecrypt.messagecrypt_menu(s)
            if message:
                reply = send_to_router(user, message).strip(b"\n")
                user = actions.messagecrypt.messagecrypt_handle_reply(s, reply)
        elif msg.lower() == b"read or post important announcements":
            message = actions.board.board_menu(s)
            if message:
                reply = send_to_router(user, message).strip(b"\n")
                user = actions.board.board_handle_reply(s, reply)
        elif msg.lower() == b"view the employee register":
            message = actions.user.user_list_menu(s)
        if user is not None:
            user.update()


def login_menu(s):
    s.send(b"First name?\n")
    first_name = s.recv(1024).strip(b"\n").decode("utf-8")
    s.send(b"Last name?\n")
    last_name = s.recv(1024).strip(b"\n").decode("utf-8")
    s.send(b"Password?\n")
    password = s.recv(1024).strip(b"\n").decode("utf-8")
    return actions.user.login(first_name, last_name, password)
    

def register_menu(s):
    s.send(b"First name?\n")
    first_name = s.recv(1024).strip(b"\n").decode("utf-8")
    s.send(b"Last name?\n")
    last_name = s.recv(1024).strip(b"\n").decode("utf-8")
    s.send(b"Password?\n")
    password = s.recv(1024).strip(b"\n").decode("utf-8")
    if actions.user.register(first_name, last_name, password):
        s.send(b"Successfully created user!\n")
        return actions.user.login(first_name, last_name, password)
    else:
        res = actions.user.login(first_name, last_name, password)
        if res != None:
            s.send(b"Successfully logged in!\n")
            return res
        else:
            s.send(b"Wrong password!")
            return None


def send_to_router(user, obj):
    router = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    router.connect((HOST, ROUTER_PORT))
    reply = b""
    target_id = None
    if type(obj) == actions.task.Task:
        target_id = "0"
    elif type(obj) == actions.leave.Leave:
        target_id = "1"
    elif type(obj) == actions.messagecrypt.MessageCryptMessage:
        target_id = "2"
    elif type(obj) == actions.board.BoardMessage:
        target_id = "3"

    tc_state_send = transport_crypt.TransportCryptState()
    tc_state_recv = transport_crypt.TransportCryptState()

    to_send = target_id + "|||" + user.serialize() + "|||" + obj.serialize()
    totalsent = 0
    while totalsent < len(to_send):
        encoded_data = to_send[totalsent:].encode("utf-8")
        encoded_data = tc_state_send.transport_crypt(bytearray(encoded_data))
        sent = router.send(encoded_data)
        if sent == 0:
            raise RuntimeError("socket connection broken")
        totalsent = totalsent + sent
    char = b""
    while bytes(char) != b"\n":
        char = router.recv(1)
        if len(char) == 0:
            break
        char = tc_state_recv.transport_crypt(bytearray(char))
        reply += char
    router.close()
    return reply


def handle_task_reply(s, reply):
    parts = reply.split(b"|||")
    user = parts[1]
    user = actions.user.User.deserialize(user.strip(b"\n").decode("utf-8"))
    if user == None:
        s.send(b"There was an error processing your request. Please try again.\n")
        return None
    task = ""
    for action in user.last_actions:
        if action[0] == "1":
            task = action
    if task != "":
        task_parsed = actions.task.Task.deserialize(task)
        if task_parsed.request_type == "99":
            s.send(b"There was an error processing your request. Please try again.\n")
        else:
            s.send(b"Success.\n")
        if task_parsed.request_type == "2" and len(parts) > 2:
            parts_decoded = parts[2].strip(b"\n").decode("utf-8")
            parts = parts_decoded.split("||")
            response = ""
            for t in parts:
                if t[0] == "1":
                    tmp = actions.task.Task.deserialize(t)
                    out = f"Task: {tmp.name}\nDescription: {tmp.description}\n"
                    response += out
            s.send(response.encode("utf-8") + b"\n")
    else:
        s.send(b"There was an error processing your request. Please try again.\n")
    return user


def handle_leave_reply(s, reply):
    parts = reply.split(b"|||")
    user = parts[1]
    user = actions.user.User.deserialize(user.strip(b"\n").decode("utf-8"))
    leave = ""
    for action in user.last_actions:
        if action[0] == "2":
            leave = action
    if leave != "":
        leave_parsed = actions.leave.Leave.deserialize(leave)
        if leave_parsed.request_type == "99":
            s.send(b"There was an error processing your request. Please try again.\n")
        else:
            s.send(b"Success.\n")
        if leave_parsed.request_type == "2" and len(parts) > 2:
            s.send(parts[2] + b"\n")
    else:
        s.send(b"There was an error processing your request. Please try again.\n")
    return user



if __name__ == "__main__":
    if not os.path.isfile("key.pem") or not os.path.isfile("cert.pem"):
        os.system("openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 3650 -nodes -subj '/C=XX/ST=StateName/L=CityName/O=CompanyName/OU=CompanySectionName/CN=CommonNameOrHostname'")
    ThreadingTCPServer.allow_reuse_address = True
    server = ThreadingTCPServer((HOST,IN_PORT),Echohandler)
    server.socket = ssl.wrap_socket(server.socket, certfile='./cert.pem', keyfile='./key.pem', server_side=True, ssl_version=ssl.PROTOCOL_TLSv1_2)
    server.serve_forever()
