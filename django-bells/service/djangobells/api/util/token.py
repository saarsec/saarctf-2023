import hashlib

class Token():

    def __init__(self, nonce, time_stamp):
        self.nonce = nonce
        self.time_stamp = time_stamp

    def log(self):
        print(f"Used nonce ({self.nonce}) at time {self.time_stamp}")

    def create_token(self):
        return hashlib.md5(str(self.nonce).encode("utf-8")).hexdigest()
    
    

