import actions.user

class Leave:

    def __init__(self, ident, request_type, start_date, end_date, reason, destination, emergency_phone): 
        self.ident = ident
        self.request_type = request_type
        self.start_date = start_date
        self.end_date = end_date
        self.reason = reason
        self.destination = destination
        self.emergency_phone = emergency_phone


    def serialize(self):
        res = ""
        res += self.ident
        res += "|" + self.request_type
        res += "|" + self.start_date 
        res += "|" + self.end_date
        res += "|" + self.reason
        res += "|" + self.destination
        res += "|" + self.emergency_phone
        return res


    def deserialize(data):
        parts = data.split("|")
        ident = parts[0]
        request_type = parts[1]
        start_date = parts[2]
        end_date = parts[3]
        reason = parts[4]
        destination = parts[5]
        emergency_phone = parts[6]
        return Leave(ident, request_type, start_date, end_date, reason, destination, emergency_phone)


def leave_menu(s):
    s.send(b"Take time off\n")
    s.send(b"Cancel holiday\n")
    s.send(b"Check current bookings\n")
    msg = s.recv(1024).strip(b"\n")
    if not msg:
        return None
    if msg.lower() == b"take time off":
        return create_holiday(s)
    if msg.lower() == b"cancel holiday":
        return cancel_holiday(s)
    if msg.lower() == b"check current bookings":
        return check_holidays(s)


def create_holiday(s):
    s.send(b"Start date?\n")
    start = s.recv(1024).strip(b"\n").decode("utf-8")
    s.send(b"End date?\n")
    end = s.recv(1024).strip(b"\n").decode("utf-8")
    s.send(b"Why do you want to take holiday?\n")
    reason = s.recv(1024).strip(b"\n").decode("utf-8")
    s.send(b"Where will you go?\n")
    destination = s.recv(1024).strip(b"\n").decode("utf-8")
    s.send(b"How can we reach you during your holiday? Please enter your phone number:\n")
    emergency = s.recv(1024).strip(b"\n").decode("utf-8")
    if start and end and reason and destination and emergency:
        start =  actions.user.sanitize(start)
        end = actions.user.sanitize(end)
        reason =  actions.user.sanitize(reason)
        destination =  actions.user.sanitize(destination)
        emergency =  actions.user.sanitize(emergency)
        leave = Leave("2", "0", start, end, reason, destination, emergency)
        return leave
    return None


def cancel_holiday(s):
    s.send(b"Start date?\n")
    start = s.recv(1024).strip(b"\n").decode("utf-8")
    s.send(b"End date?\n")
    end = s.recv(1024).strip(b"\n").decode("utf-8")
    if start and end:
        start =  actions.user.sanitize(start)
        end = actions.user.sanitize(end)
        leave = Leave("2", "1", start, end, " ", " ", " ")
        return leave
    return None


def check_holidays(s):
    start = "01-01-99"
    end = "01-01-99"
    leave = Leave("2", "2", start, end, " ", " ", " ")
    return leave
