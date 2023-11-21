import sys

from Crypto.Cipher import AES

import gamelib
from gamelib import *


# See the "SampleServiceInterface" from gamelib for a bigger example
# See https://gitlab.saarsec.rocks/saarctf/gamelib/-/blob/master/docs/howto_checkers.md for documentation.

class PasteableInterface(ServiceInterface):
    name = 'Pasteable'
    flag_id_types = ['username']

    def check_integrity(self, team: Team, tick: int) -> None:
        try:
            assert_requests_response(requests.get('http://{}:8080/'.format(team.ip), timeout=gamelib.TIMEOUT),
                                     'text/html; charset=utf-8')
        except IOError:
            raise OfflineException('Could not retrieve front-page')

    def store_flags(self, team: Team, tick: int):
        if self.load(team, tick, 'paste_info') is not None:
            print(f"Flag for team {team}, tick {tick} already stored, skipping")
            return 0

        try:
            cred_info = self.load(team, tick, 'credentials')
            sess = requests.session()
            if cred_info is not None:
                username, password_hash = cred_info
                print(f"Got login credentials (user={username}) for login flow")

                # Login flow
                response = assert_requests_response(
                    sess.post('http://{}:8080/func/challenge.php'.format(team.ip), data={'username': username},
                              timeout=gamelib.TIMEOUT),
                    'text/html; charset=utf-8'
                )

                print(f"Request was sent. Received challenge: {response.text}")

                challenge = bytes.fromhex(response.text)

                key = bytes.fromhex(password_hash)
                iv = key[:16]
                solution = AES.new(key, AES.MODE_CBC, iv=iv).decrypt(challenge).strip().decode()

                print(f"Calculated solution: {solution}")

                response = assert_requests_response(
                    sess.post('http://{}:8080/func/login.php'.format(team.ip),
                              data={'username': username, 'solution': solution}, timeout=gamelib.TIMEOUT),
                    'text/html; charset=utf-8'
                )

                assert response.status_code == 200

            else:
                print("Did not receive any credentials")

                # New User flow
                username = self.get_flag_id(team, tick, 0)
                password = usernames.generate_password()
                password_hash = hashlib.sha256(password.encode()).hexdigest()

                print(f"Generated new user: username={username}, phash={password_hash}")

                response = assert_requests_response(
                    sess.post('http://{}:8080/func/register.php'.format(team.ip),
                              data={'username': username, 'password': password_hash}, timeout=gamelib.TIMEOUT),
                    'text/html; charset=utf-8'
                )

                assert response.status_code == 200
                self.store(team, tick, 'credentials', [username, password_hash])


            response = assert_requests_response(
                sess.get('http://{}:8080/admin/paste/'.format(team.ip),
                         data={'username': username, 'password': password_hash}, timeout=gamelib.TIMEOUT),
                'text/html; charset=utf-8'
            )

            assert 'id="id"' in response.text
            # HTML-parsing from hell :D But we only need a single value
            paste_id = response.text.split('id="id" value="', maxsplit=1)[1].split('"', maxsplit=1)[0]

            print(f"Parsed PasteID: id={paste_id}")

            flag = self.get_flag(team, tick, 1)
            paste_title = usernames.generate_name(sep=' ')
            paste_password = usernames.generate_password()

            print(f"Paste information: title={paste_title}, passphrase={paste_password}")

            response = assert_requests_response(
                sess.post('http://{}:8080/func/paste.php'.format(team.ip),
                          data={
                              'title': paste_title,
                              'content': flag,
                              'password': paste_password,
                              'id': paste_id
                          }, timeout=gamelib.TIMEOUT),
                'text/html; charset=utf-8'
            )

            assert 'success' in response.text.lower()
            self.store(team, tick, 'paste_info', [paste_id, paste_password])
            return 1  # One flag was stored successfully !
        except IOError:
            raise OfflineException('Could not register')

    def retrieve_flags(self, team: Team, tick: int):
        try:
            username, password_hash = self.load(team, tick, 'credentials')
            paste_id, paste_password = self.load(team, tick, 'paste_info')
        except TypeError:  # we get a type-error if we try to parse a `None` into two values
            raise FlagMissingException(f"Cannot retrieve flag for tick {tick}, it was never set")
        try:
            print(f"Trying to retrieve flags with username={username}")

            sess = requests.Session()
            response = assert_requests_response(
                sess.post('http://{}:8080/func/challenge.php'.format(team.ip), data={'username': username},
                          timeout=gamelib.TIMEOUT),
                'text/html; charset=utf-8'
            )

            print(f"Request was sent. Received challenge: {response.text}")

            challenge = bytes.fromhex(response.text)

            key = bytes.fromhex(password_hash)
            iv = key[:16]
            solution = AES.new(key, AES.MODE_CBC, iv=iv).decrypt(challenge).strip().decode()

            print(f"Calculated solution: {solution}")

            response = assert_requests_response(
                sess.post('http://{}:8080/func/login.php'.format(team.ip),
                          data={'username': username, 'solution': solution}, timeout=gamelib.TIMEOUT),
                'text/html; charset=utf-8'
            )

            assert response.status_code == 200

            response = assert_requests_response(
                sess.get('http://{}:8080/admin/home/'.format(team.ip), timeout=gamelib.TIMEOUT),
                'text/html; charset=utf-8'
            )

            flag = self.get_flag(team, tick, 1)
            if flag not in response.text:
                raise FlagMissingException("Flag not found")

            return 1
        except IOError:
            raise OfflineException('Could not login')


if __name__ == '__main__':
    # USAGE: python3 interface.py                      # test against localhost
    # USAGE: python3 interface.py 1.2.3.4              # test against IP
    # USAGE: python3 interface.py 1.2.3.4 retrieve     # retrieve last 10 ticks (for exploits relying on checker interaction)
    # (or use gamelib/run-checkers to test against docker container)
    team = Team(1, 'TestTeam', sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1')
    service = PasteableInterface(1)

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
