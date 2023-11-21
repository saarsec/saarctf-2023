import email
import http.client
import random
import string
from typing import Optional, List, Tuple, Union, Dict

import redis
import requests

TIMEOUT = 7

# We need to patch a function in http.client, so that this broken redis header "$123\r\n" is properly ignored.
# FF and Chrome are better at this.
original_parse_headers = http.client.parse_headers


def new_parse_headers(fp, _class=http.client.HTTPMessage):
    original = original_parse_headers(fp, _class)
    hstring = str(original)
    if hstring.startswith('\n$'):
        i = 2
        while i < len(hstring):
            if '0' <= hstring[i] <= '9':
                i += 1
            elif hstring[i] == '\n' and i > 2:
                return email.parser.Parser(_class=_class).parsestr(hstring[i + 1:])
            else:
                return original
    return original


setattr(http.client, 'parse_headers', new_parse_headers)


# END OF PATCHES


def modify_location(location: str, mods: int) -> str:
    for _ in range(mods):
        i = random.randint(0, len(location) - 1)
        location = location[:i] + random.choice(string.ascii_letters) + location[i + 1:]
    return location


class RedisConnector:
    def __init__(self, target: str, port: int, verbose=False):
        self.target = target
        self.port = port
        self.conn = redis.Redis(target, port, single_connection_client=True, socket_connect_timeout=TIMEOUT)
        self.username: Optional[str] = None
        self.verbose = verbose

    def __enter__(self) -> 'RedisConnector':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def execute_command(self, *args):
        if self.verbose:
            print('> REDIS', args)
        results = self.conn.execute_command(*args)
        if self.verbose:
            print('<', results)
        return results

    def ping(self):
        result = self.execute_command('PING')
        assert result is True, 'PING not responded'

    def lolwut(self, version=None):
        if version:
            return self.execute_command('LOLWUT', 'VERSION', str(version))
        else:
            return self.execute_command('LOLWUT')

    def new_user(self, username: str, password: str):
        result = self.execute_command('NEWUSER', username, password)
        assert result == b'OK', 'NEWUSER failed'

    def auth(self, username: str, password: str):
        result = self.execute_command('AUTH', username, password)
        assert result is True, 'AUTH failed'
        self.username = username

    def get(self, key):
        return self.execute_command('LEGACY_GET', key)

    def set(self, key: str, value):
        if self.verbose:
            print('> REDIS', ['set', key, value])
        result = self.conn.setnx(key, value)
        if self.verbose:
            print('<', result)
        assert result is True, 'SETNX failed'

    def lpush(self, key, value):
        if self.verbose:
            print('> REDIS', ['lpush', key, value])
        result = self.conn.lpush(key, value)
        if self.verbose:
            print('<', result)
        assert result >= 1, 'LPUSH failed'

    def sadd(self, key, value):
        if self.verbose:
            print('> REDIS', ['sadd', key, value])
        result = self.conn.sadd(key, value)
        if self.verbose:
            print('<', result)
        return result

    def hsetnx(self, key, name, value):
        if self.verbose:
            print('> REDIS', ['hsetnx', key, name, value])
        result = self.conn.hsetnx(key, name, value)
        if self.verbose:
            print('<', result)
        return result

    def incr(self, key, value: int):
        if self.verbose:
            print('> REDIS', ['incr', key, value])
        result = self.conn.incr(key, value)
        if self.verbose:
            print('<', result)
        return result

    def create_party(self, party_id, name, guests: List[str], food: List[str]):
        self.set(f'party:{party_id}:organisator', self.username)
        self.set(f'party:{party_id}:name', name)
        for guest in guests:
            self.sadd(f'party:{party_id}:guests', guest)
        for item in food:
            self.sadd(f'party:{party_id}:food', item)

    def create_fire(self, fire_id, country: str, location: str, content: str, party_id: str):
        self.hsetnx(f'fire:{fire_id}', 'country', country)
        self.hsetnx(f'fire:{fire_id}', 'location', location)
        self.hsetnx(f'fire:{fire_id}', 'content', content)
        self.set(f'fire:{fire_id}:wood', 0)
        self.lpush(f'country:{country}:fires', fire_id)
        self.set(f'party:{party_id}:fire_id', fire_id)

    def firealarm(self, fire_id) -> List[bytes]:
        result = self.execute_command('FIREALARM', f'fire:{fire_id}')
        assert type(result) is list
        return result

    def read_alarms(self) -> List[bytes]:
        result = self.execute_command('LRANGE', f'user:{self.username}:alarms', 0, -1)
        assert type(result) is list
        return result

    def read_profile(self) -> List:
        results = [
            self.get(f'user:{self.username}:name'),
            self.get(f'user:{self.username}:dishes'),
            self.get(f'user:{self.username}:dishes_cooked'),
            self.execute_command('LRANGE', f'user:{self.username}:watch_locations', '0', '-1')
        ]
        assert results[0] == self.username.encode()
        return results

    def read_party(self, party_id: str) -> List:
        results = [
            self.execute_command('LEGACY_GET', f'party:{party_id}:name'),
            self.execute_command('LEGACY_GET', f'party:{party_id}:organisator'),
            self.execute_command('LEGACY_GET', f'party:{party_id}:fire_id'),
            self.execute_command('SMEMBERS', f'party:{party_id}:guests'),
            self.execute_command('SMEMBERS', f'party:{party_id}:food'),
        ]
        assert type(results[3]) is set, 'SMEMBERS guests must be array'
        assert type(results[4]) is set, 'SMEMBERS food must be array'
        return results

    def unauth_lrange(self, key, limit=100) -> List:
        return self.execute_command('LRANGE', key, 0, limit) or []


class HttpConnector:
    def __init__(self, target: str, port: int, verbose=False):
        self.target = target
        self.port = port
        self.session = requests.Session()
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.verbose = verbose

    def __enter__(self) -> 'HttpConnector':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def http_get(self, path) -> requests.Response:
        return self.session.get(f'http://{self.target}:{self.port}/', timeout=TIMEOUT)

    def parse_results(self, content: bytes, pos=0, limit=-1) -> Tuple[List, int]:
        results = []
        while limit != 0 and pos < len(content):
            rn = content.index(b'\r\n', pos)
            if content[pos] == ord('-'):
                results.append(AssertionError(content[pos + 1:rn].decode()))
                pos = rn + 2
            elif content[pos] == ord('$'):
                l = int(content[pos + 1:rn].decode())
                if l < 0:
                    results.append(None)
                    pos = rn + 2
                else:
                    results.append(content[rn + 2:rn + 2 + l])
                    pos = rn + 4 + l
            elif content[pos] == ord('+'):
                results.append(content[pos + 1:rn])
                pos = rn + 2
            elif content[pos] == ord(':'):
                results.append(int(content[pos + 1:rn].decode()))
                pos = rn + 2
            elif content[pos] == ord('*'):
                l = int(content[pos + 1:rn].decode())
                pos = rn + 2
                elements, pos = self.parse_results(content, pos, l)
                results.append(elements)
            else:
                print('COULD NOT PARSE:', content[pos:], content)
                raise AssertionError('Invalid char in redis http response')
            limit -= 1
        return results, pos

    def execute_commands(self, commands: List[List]) -> List:
        if self.verbose:
            print('> HTTP', commands)
        serialized = []
        for command in commands + [['QUIT']]:
            serialized.append(f'*{len(command)}\r\n'.encode())
            for x in command:
                if not isinstance(x, bytes):
                    x = str(x).encode()
                serialized.append(f'${len(x)}\r\n'.encode() + x + b'\r\n')
        response = self.session.post(f'http://{self.target}:{self.port}/api', data=b''.join(serialized), timeout=TIMEOUT)
        assert response.status_code == 200, f'Wrong status code: {response.status_code}'
        results, _ = self.parse_results(response.content)
        while len(results) > 0 and type(results[0]) is AssertionError and results[0].args[0].startswith('ERR unknown command '):
            results = results[1:]
        if self.verbose:
            for r in results[:len(commands)]:
                print('<', r)
        return results[:len(commands)]

    def execute_commands_assert(self, commands: List[List]) -> List:
        results = self.execute_commands(commands)
        for r in results:
            if type(r) is AssertionError:
                raise r
        return results

    def ping(self):
        assert self.execute_commands_assert([['PING']])[0] == b'PONG', 'HTTP PING failed'

    def lolwut(self):
        return self.execute_commands([['LOLWUT']])

    def new_user(self, username: str, password: str):
        result = self.execute_commands_assert([['NEWUSER', username, password]])
        assert result[0] == b'OK', 'NEWUSER failed'

    def auth(self, username: str, password: str):
        result = self.execute_commands_assert([['AUTH', username, password]])
        assert result[0] == b'OK', 'AUTH failed'
        self.username = username
        self.password = password

    def get(self, key):
        return self.execute_commands_assert([['LEGACY_GET', key]])[0]

    def set(self, key: str, value):
        self.execute_commands_assert([
            ['AUTH', self.username, self.password],
            ['SETNX', key, value]
        ])

    def lpush(self, key, value):
        results = self.execute_commands_assert([
            ['AUTH', self.username, self.password],
            ['LPUSH', key, value]
        ])
        assert results[1] >= 1, 'LPUSH failed'

    def sadd(self, key, value):
        return self.execute_commands_assert([
            ['AUTH', self.username, self.password],
            ['SADD', key, value]
        ])[1]

    def hsetnx(self, key, name, value):
        return self.execute_commands_assert([
            ['AUTH', self.username, self.password],
            ['HSETNX', key, name, value]
        ])[1]

    def incr(self, key, value: int):
        return self.execute_commands_assert([
            ['AUTH', self.username, self.password],
            ['INCRBY', key, value]
        ])[1]

    def create_party(self, party_id, name, guests: List[str], food: List[str]):
        self.set(f'party:{party_id}:organisator', self.username)
        self.set(f'party:{party_id}:name', name)
        for guest in guests:
            self.sadd(f'party:{party_id}:guests', guest)
        for item in food:
            self.sadd(f'party:{party_id}:food', item)

    def create_fire(self, fire_id, country: str, location: str, content: str, party_id: str):
        self.hsetnx(f'fire:{fire_id}', 'country', country)
        self.hsetnx(f'fire:{fire_id}', 'location', location)
        self.hsetnx(f'fire:{fire_id}', 'content', content)
        self.set(f'fire:{fire_id}:wood', 0)
        self.lpush(f'country:{country}:fires', fire_id)
        self.set(f'party:{party_id}:fire_id', fire_id)

    def firealarm(self, fire_id) -> List[bytes]:
        results = self.execute_commands_assert([
            ['AUTH', self.username, self.password],
            ['FIREALARM', f'fire:{fire_id}']
        ])
        assert type(results[1]) is list
        return results[1]

    def read_alarms(self) -> List[bytes]:
        results = self.execute_commands_assert([
            ['AUTH', self.username, self.password],
            ['LRANGE', f'user:{self.username}:alarms', 0, -1]
        ])
        assert type(results[1]) is list
        return results[1]

    def read_profile(self) -> List:
        results = self.execute_commands_assert([
            ['AUTH', self.username, self.password],
            ['LEGACY_GET', f'user:{self.username}:name'],
            ['LEGACY_GET', f'user:{self.username}:dishes'],
            ['LEGACY_GET', f'user:{self.username}:dishes_cooked'],
            ['LRANGE', f'user:{self.username}:watch_locations', '0', '-1']
        ])
        assert results[1] == self.username.encode()
        return results[1:]

    def read_party(self, party_id: str) -> List:
        results = self.execute_commands_assert([
            ['AUTH', self.username, self.password],
            ['LEGACY_GET', f'party:{party_id}:name'],
            ['LEGACY_GET', f'party:{party_id}:organisator'],
            ['LEGACY_GET', f'party:{party_id}:fire_id'],
            ['SMEMBERS', f'party:{party_id}:guests'],
            ['SMEMBERS', f'party:{party_id}:food'],
        ])
        assert type(results[4]) is list, 'SMEMBERS guests must be array'
        assert type(results[5]) is list, 'SMEMBERS food must be array'
        return results[1:]

    def unauth_lrange(self, key, limit=100) -> List:
        return self.execute_commands_assert([
            ['LRANGE', key, 0, limit]
        ])[0] or []


def get_random_connector(target: str, port: int, offset: int) -> Union[RedisConnector, HttpConnector]:
    if offset % 2 == 0:
        return RedisConnector(target, port, verbose=True)
    return HttpConnector(target, port, verbose=True)
