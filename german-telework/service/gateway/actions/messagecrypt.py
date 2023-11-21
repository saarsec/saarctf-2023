import base64
import actions.user
import uuid

class MessageCryptMessage:
    def __init__(self, action_id, employee_id_recipient=None, plaintext_bytes=None, ciphertext_bytes=None):
        self.action_id = action_id
        if self.action_id == "e": 
            self.employee_id_recipient = employee_id_recipient
            self.plaintext_bytes = plaintext_bytes
        elif self.action_id == "d": 
            self.ciphertext_bytes = ciphertext_bytes
        else:
            raise Exception("Bad action_id")

    def serialize(self):
        res = self.action_id
        if self.action_id == "e": 
            res += "|" + self.employee_id_recipient.bytes.hex()
            res += "|" + base64.b64encode(self.plaintext_bytes).decode("utf-8")
        elif self.action_id == "d": 
            res += "|" + base64.b64encode(self.ciphertext_bytes).decode("utf-8")
        else:
            raise Exception("Bad action_id")
        return res

    @staticmethod
    def deserialize(data):
        parts = data.split("|")
        action_id = parts[1]
        if action_id == "e": 
            try:
                employee_id_recipient_uuid = uuid.UUID(hex=parts[2])
            except Exception as e:
                raise Exception("Bad employee ID")
            return MessageCryptMessage(
                action_id=action_id,
                employee_id_recipient=employee_id_recipient_uuid,
                plaintext_bytes=base64.b64decode(bytes(parts[3]))
            )
        elif action_id == "d": 
            return MessageCryptMessage(
                action_id=action_id,
                ciphertext_bytes=base64.b64decode(bytes(parts[2]))
            )
        else:
            raise Exception("Bad action_id")

def messagecrypt_menu(s):
    s.send(b"Encrypt a message to someone else\n")
    s.send(b"Decrypt a message I received\n")
    msg = s.recv(1024).strip()
    if not msg:
        return None
    if msg.lower() == b"encrypt a message to someone else":
        return messagecrypt_enc(s)
    if msg.lower() == b"decrypt a message i received":
        return messagecrypt_dec(s)

def messagecrypt_enc(s):
    s.send(b"Recipient's employee ID?\n")
    employee_id_recipient = s.recv(1024).strip().decode("utf-8").replace("-", "")
    s.send(b"Message Body? (up to 512 bytes, base64)\n")
    plaintext = s.recv(1024).strip()
    if employee_id_recipient and plaintext:
        try:
            employee_id_recipient_uuid = uuid.UUID(hex=employee_id_recipient)
        except Exception as e:
            return None
        return MessageCryptMessage(
            action_id="e",
            employee_id_recipient=employee_id_recipient_uuid,
            plaintext_bytes=base64.b64decode(plaintext)
        )
    return None

def messagecrypt_dec(s):
    s.send(b"Ciphertext? (up to 512 bytes, base64)\n")
    ciphertext = s.recv(1024).strip()
    if ciphertext:
        return MessageCryptMessage(
            action_id="d",
            ciphertext_bytes=base64.b64decode(ciphertext)
        )
    return None

def messagecrypt_handle_reply(s, reply):
    if len(reply) == 0:
        s.send(b"Got no response from the messagecrypt backend. Sorry.\n")
        return None
    error_code = reply[0:2]
    if reply[1] == 0x53: 
        s.send(f"The following error occurred: 0x53{reply[0]:02x}\n".encode('utf-8'))
        return None
    elif reply[1] == 0x47: 
        parts = reply[2:].split(b"|||")
        user = actions.user.User.deserialize(parts[0].strip().decode("utf-8"))
        if reply[0] == ord('e'): 
            s.send(b"This is your encrypted message:\n")
            s.send(parts[1])
            s.send(b"\n")
        elif reply[0] == ord('d'): 
            s.send(b"This is your decrypted message:\n")
            s.send(base64.b64decode(parts[1]))
            s.send(b"\n")
        return user
    else:
        s.send(b"Got a bad response from the backend.")
