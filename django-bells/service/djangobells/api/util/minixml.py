
class XMLException(Exception):
    pass

class Tag:

    def __init__(self, name: str = "", value: str = "", closing: bool = False, value_token: bool = False):
        self.name = name
        self.value = value
        self.closing = closing
        self.value_token = value_token
    
    def __str__(self):
        return f"{self.name}, {self.value}\n"
    
    def __repr__(self):
        return f"{self.name}, {self.value}\n"


class miniXML:

    def __init__(self: 'miniXML', xml_string: str, secure: bool = True):
        self.xml_string = xml_string
        self.pos = 0
        self.len = len(xml_string)
        self.secure = secure
        self.xml_dict = {}
        self.keys = []
        self.xe = {"&gt;": ">", "&lt": "<", "&amp;": "&", "&apos;": "'", "&quot": '"'}


    def peak(self, next: int = 1):
        if self.pos + next > self.len:
            raise IndexError
        return self.xml_string[self.pos : self.pos + next]
    
    def eat(self, next: int = 1):
        if self.pos + next > self.len:
            raise IndexError
        self.pos =  self.pos + next
        return self
    
    def peak_until(self, c: chr):
        i = 1
        while True:
            if self.peak(i)[-1] == c:
                return self.peak(i-1)
            i += 1
    
    def eat_until(self, c: str):
        i = 1
        while True:
            if self.peak(i)[-1] == c:
                self.eat(i-1)
                return self
            i += 1

    def eat_chr(self, c: str):
        if self.peak() == c:
            self.eat()
            return
        raise XMLException

    def parse_tag(self):
        self.eat_until_not_ws()
        if self.peak(2) != "</" and self.peak() == "<": # Opening Tag e.g <root>
            self.eat()
            name = self.peak_until(">")
            self.eat_until(">")
            self.eat()
            return Tag(name=name)
        if self.peak(2) == "</": # Closing Tag e.g </root>
            self.eat(2)
            name = self.peak_until(">")
            self.eat_until(">")
            self.eat()
            return Tag(name=name, closing=True)
        value = self.peak_until("<")
        self.eat_until("<")
        for key, _ in self.xe.items():
            if key in value:
                value = self.replace(value, key)
        return Tag(value=value, value_token=True)

    
    def replace(self, value, key):
        if self.secure and len(self.xe) > 5:
            raise XMLException
        return value.replace(key, self.xe[key])


    def parse_to_token(self):
        tokens = []
        while self.pos < self.len:
            if self.peak() == "\n":
                self.eat()
            else:
                tokens.append(self.parse_tag())
        return tokens

    def check_tokens(self, tokens: list[Tag]):
        for i in range(len(tokens)):
            token = tokens[i]
            if token.value_token:
                continue
            if not token.closing:
                for j in range(i, len(tokens)):
                    token_2 = tokens[j]
                    if token_2.closing and token.name == token_2.name:
                        break
                else:
                    raise XMLException
            
            
    def parse(self):
        self.eat_XMLdecl()
        self.read_doctype()
        tokens = self.parse_to_token()
        self.check_tokens(tokens)
        self.create_keys(tokens)
        self.xml_dict = self.get_values(0,tokens, {})

    def get_values(self, start: int, tokens: list[Tag], vals: dict) -> dict:
        if tokens[start].name == tokens[start+2].name and not tokens[start].closing and tokens[start+2].closing and tokens[start+1].value_token:
            new = {}
            new[tokens[start].name] = tokens[start+1].value 
            return new
        elif tokens[start].name == tokens[start+1].name and not tokens[start].closing and tokens[start+1].closing:
            new = {}
            new[tokens[start].name] = ""
            return new
        else:
            for end in range(len(tokens)):
                if tokens[start].name == tokens[end].name and not tokens[start].closing and tokens[end].closing:
                    new = {}
                    k = start+1
                    counter = 0
                    while k<len(tokens)-2:
                        if counter > 1000:
                            raise XMLException
                        new.update(self.get_values(k, tokens, vals))
                        if tokens[k].name == tokens[k+2].name and not tokens[k].closing and tokens[k+2].closing and tokens[k+1].value_token:
                            k += 3
                        elif tokens[k].name == tokens[k+1].name and not tokens[k].closing and tokens[k+1].closing:
                            k += 2
                        counter +=1
                    vals[tokens[start].name] = new
                    return vals

    def create_keys(self, tokens: list[Tag]):
        for token in tokens:
            if not token.closing and not token.value_token:
                self.keys.append(token.name)

    def get_from_dict(self, key: str, d: dict):
        for k, value in d.items():
            if k == key:
                return value
            if isinstance(value, dict):
                res = self.get_from_dict(key, value)
                if res is not None:
                    return res
        return None

    def get_keys(self):
        return self.keys

    def get(self, key):
        if key not in self.keys:
            raise KeyError
        return self.get_from_dict(key, self.xml_dict)

    def eat_doctype(self):
        self.eat_until_not_ws()
        try:
            while self.peak(9) == "<!DOCTYPE":
                self.eat_until(">")
                self.eat()
        except:
            pass
        return self
    
    def read_doctype(self):
        self.eat_until_not_ws()
        try:
            while self.peak(9) == "<!DOCTYPE":
                self.eat_until("E")
                self.eat()
                self.eat_until_not_ws()
                
                _, index = self.peak_until_ws()
                self.eat(index)
                self.eat_until_not_ws()
                if self.peak() == "[":
                    self.eat()
                    self.read_entity()
                #if self.peak(6) == "SYSTEM":
                    #TODO
                    #pass
                self.eat_until(">")
                self.eat()
                self.eat_until_not_ws()
        except:
            pass
        return self


    def eat_XMLdecl(self):
        self.eat_until_not_ws()
        try:
            while self.peak(2) == "<?":
                self.eat_until(">")
                self.eat()
        except:
            pass
        return self
    
    def read_entity(self):
        self.eat_until_not_ws()
        try:
            while self.peak(8) == "<!ENTITY":
                self.eat_until("Y")
                self.eat()
                self.eat_until_not_ws()
                name, index = self.peak_until_ws()
                name = name.strip()
                self.eat(index)
                self.eat_until_not_ws()
                if self.peak(6) == "SYSTEM":
                    self.eat(6)
                    self.eat_until_not_ws()
                    self.eat_chr('"')
                    path = self.peak_until("\"").replace("file://", "")
                    self.eat_until("\"")
                    self.eat()
                    file_s = ""
                    try:
                        with open(path, "rb") as f:
                            file_s = repr(f.read())    
                    except Exception as e:
                        pass
                    self.xe["&" + name + ";"] = file_s
                self.eat_until_not_ws()
                self.eat_chr(">")
                self.eat_until_not_ws()
                self.eat_chr("]")
        except:
            pass
        return self


    def eat_until_not_ws(self):
        while self.len > 0:
            if not self.peak() == " " and not self.peak() == "\t" and not self.peak() == "\n":
                return self
            self.eat()

    def peak_until_ws(self):
        i = 1
        while self.len > 0:
            if self.peak(i)[-1] == " " or self.peak(i)[-1] == "\t":
                return (self.peak(i), i-1)
            i += 1
        

    def get_xml_string(self):
        return self.xml_string[self.pos::]
    

