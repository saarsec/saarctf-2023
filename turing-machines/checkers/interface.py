import binascii

import requests

from gamelib import *

try:
    from .turinggen import generate_random_machine, TuringMachine, check_cpp_code
except ImportError:
    from turinggen import generate_random_machine, TuringMachine, check_cpp_code


PORT = 2080


class TuringMachinesServiceInterface(ServiceInterface):
    name = 'TuringMachines'

    def check_integrity(self, team: Team, tick: int):
        assert_requests_response(requests.get(f'http://{team.ip}:{PORT}/', timeout=TIMEOUT), 'text/html; charset=UTF-8')

    def store_flags(self, team: Team, tick: int):
        flag = self.get_flag(team, tick)
        sess = requests.Session()
        print(f'GET http://{team.ip}:{PORT}/machine/new')
        assert_requests_response(sess.get(f'http://{team.ip}:{PORT}/machine/new', timeout=TIMEOUT), 'text/html; charset=UTF-8')
        # generate proper machine
        machine = generate_random_machine(flag)
        print('Machine tape: ', binascii.hexlify(machine.initial_tape).decode())
        print('Final tape:   ', binascii.hexlify(machine.final_tape()).decode())
        print(f'POST http://{team.ip}:{PORT}/machine/new ...')
        response = sess.post(f'http://{team.ip}:{PORT}/machine/new', data={'name': flag, 'states': machine.json_states()}, timeout=TIMEOUT)
        assert_requests_response(response, 'text/html; charset=UTF-8')
        print('-->', response.url)
        assert response.url.startswith(f'http://{team.ip}:{PORT}/machines/'), "/machine/new did not redirect"
        ident = response.url.split('/')[-1]
        print('Ident:', ident)
        assert len(ident) == 32, 'Machine ident has wrong length'
        self.store(team, tick, 'ident', ident)
        # compile machine
        print(f'POST http://{team.ip}:{PORT}/machine/update')
        response = sess.post(f'http://{team.ip}:{PORT}/machine/update', data={'action': 'compile', 'ident': ident, 'name': flag, 'states': machine.json_states()}, timeout=TIMEOUT)
        assert_requests_response(response, 'text/plain; charset=utf-8')
        assert 'Content-Disposition' in response.headers
        assert response.headers['Content-Disposition'].endswith('filename="machine.cpp"')
        check_cpp_code(machine, response.text)
        # get test program
        print(f'GET http://{team.ip}:{PORT}/machine/run/{ident}')
        response = sess.get(f'http://{team.ip}:{PORT}/machine/run/{ident}', timeout=TIMEOUT)
        assert_requests_response(response, 'text/html; charset=UTF-8')
        print(f'POST http://{team.ip}:{PORT}/machine/run/{ident} (action=program)')
        response = sess.post(f'http://{team.ip}:{PORT}/machine/run/{ident}', data={
            'action': 'program',
            'ident': ident,
            'tape': binascii.hexlify(machine.initial_tape).decode()
        }, timeout=TIMEOUT)
        assert_requests_response(response, 'text/plain; charset=utf-8')
        assert 'Content-Disposition' in response.headers
        assert response.headers['Content-Disposition'].endswith('filename="machine_test.cpp"')
        # run test program remote
        print(f'POST http://{team.ip}:{PORT}/machine/run/{ident} (action=run)')
        response = sess.post(f'http://{team.ip}:{PORT}/machine/run/{ident}', data={
            'action': 'run',
            'ident': ident,
            'tape': binascii.hexlify(machine.initial_tape).decode()
        }, timeout=TIMEOUT)
        assert_requests_response(response, 'text/html; charset=utf-8')
        assert 'compiler or runtime error' not in response.text, 'compiler or runtime error'
        assert "Final state: &#39;" + machine.final_state + "&#39;" in response.text, 'Final state not reached'
        p = response.text.find('Final tape ')
        assert p > 0, 'No final tape'
        content = response.text[p+12:]
        length, content = content.split(' ', 1)
        length = int(length)
        lines = content[8:].split('\n')
        final_tape_hex = lines[:(length+15)//16]
        final_tape_hex = ''.join(final_tape_hex).replace(' ', '').replace('\n', '')
        final_tape = binascii.unhexlify(final_tape_hex)
        print('Resulting tape: ', binascii.hexlify(final_tape).decode())
        print('Expected tape:  ', binascii.hexlify(machine.final_tape()).decode())
        print('Initial tape:   ', binascii.hexlify(machine.initial_tape).decode())

        assert final_tape == machine.final_tape(), 'Final tape is wrong'

    def retrieve_flags(self, team: Team, tick: int):
        ident = self.load(team, tick, 'ident')
        if not ident:
            raise FlagMissingException('flag was not stored last tick')
        flag = self.get_flag(team, tick)
        sess = requests.Session()
        response = sess.get(f'http://{team.ip}:{PORT}/machines/{ident}', timeout=TIMEOUT)
        assert_requests_response(response, 'text/html; charset=UTF-8')
        assert flag in response.text, "Flag missing in /machine/edit"


if __name__ == '__main__':
    team = Team(1, 'Local', '127.0.0.1')
    interface = TuringMachinesServiceInterface(12)
    for tick in range(1, 4):
        print('Check ...')
        interface.check_integrity(team, tick)
        print('Store ...')
        interface.store_flags(team, tick)
        print('Retrieve ...')
        interface.retrieve_flags(team, tick)
        print('Done.')
