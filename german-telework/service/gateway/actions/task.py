import actions.user

class Task:

    def __init__(self, ident, request_type, name, description, steps_repr, epic, sprint, hours_estimated):
        self.ident = ident;
        self.request_type = request_type
        self.name = name
        self.description = description
        self.steps_repr = steps_repr
        self.epic = epic
        self.sprint = sprint
        self.hours_estimated = hours_estimated        

    
    def serialize(self):
        res = ""
        res += self.ident
        res += "|" + self.request_type
        res += "|" + self.name
        res += "|" + self.description
        res += "|" + self.steps_repr
        res += "|" + self.epic
        res += "|" + self.sprint
        res += "|" + self.hours_estimated
        return res

    
    def deserialize(data):
        parts = data.split("|")
        ident = parts[0]
        request_type = parts[1]
        name = parts[2]
        description = parts[3]
        steps_repr = parts[4]
        epic = parts[5]
        sprint = parts[6]
        hours_estimated = parts[7]
        res = Task(ident, request_type, name, description, steps_repr, epic, sprint, hours_estimated) 
        return res


def task_menu(s):
    s.send(b"Create task\n")
    s.send(b"Complete task\n")
    s.send(b"List all tasks\n")
    msg = s.recv(1024).strip(b"\n")
    if not msg:
        return None
    if msg.lower() == b"create task":
        return create_task(s)
    if msg.lower() == b"complete task":
        return complete_task(s)
    if msg.lower() == b"list all tasks":
        return check_details(s)


def create_task(s):
    s.send(b"Task name?\n")
    name = s.recv(1024).strip(b"\n").decode("utf-8")
    s.send(b"Description?\n")
    description = s.recv(1024).strip(b"\n").decode("utf-8")
    s.send(b"Steps to fulfill the task?\n")
    steps = s.recv(1024).strip(b"\n").decode("utf-8")
    s.send(b"Which epic does this task belong to?\n")
    epic = s.recv(1024).strip(b"\n").decode("utf-8")
    s.send(b"Which sprint do you want to work on this?\n")
    sprint = s.recv(1024).strip(b"\n").decode("utf-8")
    s.send(b"How many workhours do you think this takes?\n")
    hours = s.recv(1024).strip(b"\n").decode("utf-8")
    try:
        res = int(hours,10)
    except Exception as e:
        s.send(b"Invalid format for workhours!\n")
        return None
    if name and description and steps and epic and sprint and hours:
        name =  actions.user.sanitize(name)
        description =  actions.user.sanitize(description)
        steps =  actions.user.sanitize(steps)
        epic =  actions.user.sanitize(epic)
        sprint =  actions.user.sanitize(sprint)
        hours =  actions.user.sanitize(hours)
        task = Task("1", "0", name, description, steps, epic, sprint, hours)
        return task
    return None


def complete_task(s):
    s.send(b"Task name?\n")
    name = s.recv(1024).strip(b"\n").decode("utf-8")
    name = actions.user.sanitize(name)
    s.send(b"Task epic?\n")
    epic = s.recv(1024).strip(b"\n").decode("utf-8")
    epic = actions.user.sanitize(epic)
    if name:
        return Task("1", "1", name, " ", " ", epic, " ", "0")
    return None


def check_details(s):
    return Task("1", "2", " ", " ", " ", " ", " ", "0")

