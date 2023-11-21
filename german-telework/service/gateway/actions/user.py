import random
import shutil
import os
import actions.task
import uuid
import hashlib
import glob

USER_DIR = "data/users"

class User:


    def __init__(self, ident, firstname, lastname, password, employee_id, job_desc, holidays_left, last_actions=None):
        self.ident = ident
        self.firstname = firstname
        self.lastname = lastname
        self.password = password
        self.employee_id = employee_id
        self.job_desc = job_desc
        self.holidays_left = holidays_left
        if last_actions:
            self.last_actions = last_actions
        else:
            self.last_actions = []

    def update(self):
        path_name = USER_DIR + "/" + create_path(self.firstname)
        shutil.rmtree(path_name)
        self.store()


    def store(self):
        path_name = USER_DIR + "/" + create_path(self.firstname)
        if os.path.exists(path_name):
            return False
        else:
            os.makedirs(path_name)
            with open(path_name + "/user.ser", "w", encoding="utf-8") as f:
                f.write(self.serialize())
                f.write("\n")
            return True


    def serialize(self):
        res = self.ident
        res += "|" + self.firstname
        res += "|" + self.lastname
        res += "|" + self.password
        res += "|" + self.employee_id.bytes.hex()
        res += "|" + self.job_desc
        res += "|" + str(self.holidays_left)
        if self.last_actions:
            res += "||" + "||".join(self.last_actions)
        return res


    def deserialize(data):
        parts = data.split("||")
        user = None
        user_index = -1
        last_actions = []
        for entry in parts:
            if entry[0] == "0":
                user = entry
                user_index = parts.index(entry)
            else:
                last_actions.append(entry)
        if user == None or user_index == -1:
            return None
        parts.pop(user_index)
        user_parts = user.split("|")
        ident = user_parts[0]
        firstname = user_parts[1]
        lastname = user_parts[2]
        password = user_parts[3]
        employee_id = uuid.UUID(hex=user_parts[4])
        job_desc = user_parts[5]
        holidays_left = user_parts[6]
        if len(last_actions) == 0:
            return User(ident, firstname, lastname, password, employee_id, job_desc, holidays_left)
        else:
            return User(ident, firstname, lastname, password, employee_id, job_desc, holidays_left, last_actions)


    def append_action(self, action):
        action_id = action[0]
        remove_index = None
        for last_action in self.last_actions:
            if last_action[0] == action_id:
                remove_index = self.last_actions.index(last_action)
        if remove_index != None:
            self.last_actions.pop(remove_index)
        self.last_actions.append(action)


def create_path(firstname):
    path_name_base = bytes(firstname, encoding="utf-8")
    path_name = hashlib.sha256()
    path_name.update(path_name_base)
    path_name = path_name.hexdigest() 
    return path_name


def sanitize(data):
    data = data.replace("|","")
    data = data.replace(".","")
    data = data.replace("\n","")
    if len(data) == 0:
        return " "
    return data


def register(name, lastname, password):
    name = sanitize(name)
    lastname = sanitize(lastname)
    password = sanitize(password)
    u = User("0", name, lastname, password, uuid.uuid4(), "coder", 30)
    return u.store()


def login(name, lastname, password):
    name = sanitize(name)
    lastname = sanitize(lastname)
    password = sanitize(password)
    path = create_path(name)
    if not os.path.exists(USER_DIR + "/" + path + "/user.ser"):
        return None
    with open(USER_DIR + "/" + path + "/user.ser", "r", encoding="utf-8") as f:
        for line in f.readlines():
            ident = line.split("|")[0]
            if ident == "0":
                user = User.deserialize(line.strip("\n"))
                if user.lastname == lastname and user.password == password:
                    return user
                return None
    return None

def user_list_menu(s):
    s.send(b"This is the current employee list:\n")
    paths = glob.glob(f"{USER_DIR}/*/user.ser")
    for path in paths:
        with open(path) as user_file:
            user_serialized = user_file.read().strip("\n")
            user = User.deserialize(user_serialized)
            s.send(f"{user.employee_id} | {user.job_desc} | {user.firstname} | {user.lastname}\n".encode('utf-8'))
    s.send(b"End of employee list.\n")
