import base64
import uuid
import actions.user

class BoardMessage:
    def __init__(self, action_id, data=None):
        self.action_id = action_id
        if self.action_id == "c": 
            pass
        elif self.action_id == "i": 
            self.message_id = data
        elif self.action_id == "n": 
            if data.isnumeric():
                self.message_number = int(data)
            else:
                raise Exception("Bad message number")
        elif self.action_id == "p": 
            self.text = data
        else:
            raise Exception("Bad action_id")

    def serialize(self):
        res = self.action_id
        if self.action_id == "c": 
            pass
        elif self.action_id == "i": 
            res += "|" + self.message_id
        elif self.action_id == "n": 
            res += "|" + str(self.message_number)
        elif self.action_id == "p": 
            res += "|" + self.text
        else:
            raise Exception("Bad action_id")
        return res

    @staticmethod
    def deserialize(data):
        parts = data.split("|")
        action_id = parts[1]
        if action_id == "a": 
            return BoardMessage(
                action_id=action_id,
            )
        elif action_id == "p": 
            return BoardMessage(
                action_id=action_id,
                text=parts[2],
            )
        else:
            raise Exception("Bad action_id")

def board_menu(s):
    s.send(b"Get number of active announcements\n")
    s.send(b"Get announcement by ID\n")
    s.send(b"Get announcement by number\n")
    s.send(b"Post an announcement\n")
    msg = s.recv(1024).strip()
    if not msg:
        return None
    if msg.lower() == b"get number of active announcements":
        return board_get_count(s)
    if msg.lower() == b"get announcement by id":
        return board_get_message_by_id(s)
    if msg.lower() == b"get announcement by number":
        return board_get_message_by_number(s)
    if msg.lower() == b"post an announcement":
        return board_post(s)

def board_get_count(s):
    return BoardMessage(
        action_id="c",
    )

def board_get_message_by_id(s):
    s.send(b"Message ID?\n")
    data = s.recv(1024).strip().decode("utf-8")
    return BoardMessage(
        action_id="i",
        data=actions.user.sanitize(data)
    )

def board_get_message_by_number(s):
    s.send(b"Message Number?\n")
    data = s.recv(1024).strip().decode("utf-8")
    return BoardMessage(
        action_id="n",
        data=actions.user.sanitize(data)
    )
    return None

def board_post(s):
    s.send(b"Text? (up to 1000 characters)\n")
    text = s.recv(1024).strip().decode("utf-8")
    if text:
        return BoardMessage(
            action_id="p",
            data=actions.user.sanitize(text)
        )
    return None

def board_handle_reply(s, reply):
    if len(reply) == 0:
        s.send(b"Got no response from the board backend. Sorry.\n")
        return None
    error_code = reply[0:2]
    if reply[1] == 0x53: 
        s.send(f"The following error occurred: 0x53{reply[0]:02x}\n".encode('utf-8'))
        return None
    elif reply[1] == 0x47: 
        parts = reply[2:].split(b"|||")
        user = actions.user.User.deserialize(parts[0].strip().decode("utf-8"))
        if reply[0] == ord('c'): 
            count = parts[1].strip()
            s.send(b"Number of announcements: " + count + b"\n")
        elif reply[0] in [ord('i'), ord('n')]: 
            author_and_message = parts[1].rstrip()
            author_and_message_parts = author_and_message.decode("utf-8").split("|")
            try:
                first = author_and_message_parts[0]
                last = author_and_message_parts[1]
                message = author_and_message_parts[2]
            except e as Exception:
                return user
            s.send(
                (f"ANNOUNCEMENT. ATTENTION PLEASE, THIS IS {first} {last} "
                "SPEAKING TO EVERYONE. ").encode('utf-8')
            )
            s.send(message.encode("utf-8"))
            s.send(b" I REPEAT. ")
            s.send(message.encode("utf-8"))
            s.send(b" END OF ANNOUNCEMENT.\n")
        elif reply[0] == ord('p'): 
            message_id = parts[1].rstrip()
            s.send(b"Your important announcement has been filed under the ID " + message_id + b".\n")
        return user
    else:
        s.send(b"Got a bad response from the backend.")
