from gamelib import *
import sys
from pwn import remote
import requests
import urllib.parse
import uuid

# See the "SampleServiceInterface" from gamelib for a bigger example
# See https://gitlab.saarsec.rocks/saarctf/gamelib/-/blob/master/docs/howto_checkers.md for documentation.

class ExampleServiceInterface(ServiceInterface):
    name = 'Django Bells'

    def check_integrity(self, team: Team, tick: int):

        # Check that the service is online
        print(f"> GET http://{team.ip}:8000")
        r = requests.get(f"http://{team.ip}:8000", timeout=TIMEOUT)
        print(f'< {r}')
        assert_requests_response(r, 'text/html; charset=utf-8')
        # check for conditions - if an assert fails the service status is MUMBLE
        assert 'Django Bells' in r.text, 'Index Page not found'

        # Check if the report feature still works
        id = uuid.uuid4()
        print(f"> GET http://{team.ip}:8000/report?id={id}")
        r = requests.get(f"http://{team.ip}:8000/report?id={id}", timeout=TIMEOUT)
        print(f'< {r}')
        assert 'Thanks' in r.text, 'Report page not working'


    def store_flags(self, team: Team, tick: int):
        flag = self.get_flag(team, tick)
        print(f'> GET http://{team.ip}:8000/create/?post_data={urllib.parse.quote_plus(flag)}')
        r = requests.get(f"http://{team.ip}:8000/create/?post_data={urllib.parse.quote_plus(flag)}", timeout=TIMEOUT)
        print(f'< {r} ({r.url})')
        assert_requests_response(r, 'text/html; charset=utf-8')
        id = r.url.split("/")[4]
        token = r.url.split("/")[5]
        self.store(team, tick, "creds", (id,token))

    def retrieve_flags(self, team: Team, tick: int):
        flag = self.get_flag(team, tick)
        try:
            id, token = self.load(team, tick, "creds")
        except TypeError:
            raise FlagMissingException('flag not stored')
        print(f'> GET http://{team.ip}:8000/read/{id}/{token}')
        r = requests.get(f"http://{team.ip}:8000/read/{id}/{token}", timeout=TIMEOUT)
        print(f'< {r}')
        assert_requests_response(r, 'text/html; charset=utf-8')
        if flag not in r.text:
            # verbose error logging is always a good idea
            print('GOT:', r.text)
            # flag not found? Raise FlagMissingException
            raise FlagMissingException('Flag not found')
        
        # Check list endpoint
        print(f'> GET http://{team.ip}:8000/list/')
        r = requests.get(f"http://{team.ip}:8000/list/", timeout=TIMEOUT)
        print(f'< {r}')
        if id not in r.text:
            print('GOT:', r.text)
            raise FlagMissingException('List endpoint not available')


if __name__ == '__main__':
    # USAGE: python3 interface.py                      # test against localhost
    # USAGE: python3 interface.py 1.2.3.4              # test against IP
    # USAGE: python3 interface.py 1.2.3.4 retrieve     # retrieve last 10 ticks (for exploits relying on checker interaction)
    # (or use gamelib/run-checkers to test against docker container)
    team = Team(1, 'TestTeam', sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1')
    service = ExampleServiceInterface(1)

    if len(sys.argv) > 2 and sys.argv[2] == 'retrieve':
        for tick in range(1, 10):
            try:
                service.retrieve_flags(team, tick)
            except:
                pass
        sys.exit(0)

    for tick in range(1, 4):
        print(f'\n\n=== TICK {tick} ===')
        service.check_integrity(team, tick)
        service.store_flags(team, tick)
        service.retrieve_flags(team, tick)
