import json
import random
import string
import sys
import uuid

import redis.exceptions

from connectors import RedisConnector, modify_location


def random_string(n: int) -> str:
    return ''.join(random.choice(string.ascii_letters) for _ in range(n))


def check_permissions(target: str):
    with RedisConnector(target, 12345) as conn:
        x = conn.conn.get('/')
        assert x.startswith(b'Content-Type: ')

        # register a new user, add data to profile and list as new
        username = 'user' + random_string(12)
        #password = 'pass' + random_string(12)
        password = username
        conn.new_user(username, password)
        conn.auth(username, password)
        conn.set(f'user:{username}:flag', 'SAAR{flag1}')  # TODO key
        conn.lpush(f'newest:users', username)

        # create a new party with campfire
        country = random_string(12)
        location = random_string(16)
        location2 = modify_location(location, 2)
        fire_id = str(uuid.uuid4())
        party_id = str(uuid.uuid4())
        conn.create_party(party_id, 'TestParty', [username], ['SAAR{flag2}'])
        conn.create_fire(fire_id, country, location, 'SAAR{flag3}', party_id)
        # conn.set(f'party:{party_id}:fire_id', fire_id)
        conn.lpush(f'newest:countries', country)
        # conn.lpush(f'country:{country}:fires', fire_id)

        with RedisConnector(target, 12345) as conn2:
            # register firealarm
            username2 = 'ff' + random_string(12)
            #password2 = 'pass' + random_string(12)
            password2 = username2
            conn2.new_user(username2, password2)
            conn2.auth(username2, password2)
            ff_loc = json.dumps({'country': country, 'location': location2}).replace(' ', '')
            conn2.hsetnx(f'country:{country}:firefighters', username2, ff_loc)

            # add food as other account
            conn2.sadd(f'party:{party_id}:food', 'Some random food')
            # add wood
            conn.incr(f'fire:{fire_id}:wood', 1000)
            # trigger fire
            informed = conn.firealarm(fire_id)
            print('Informed firefighters:', informed)
            assert len(informed) >= 2
            assert username2.encode() in informed
            assert ff_loc.encode() in informed
            # check that fire triggered
            alarms = conn2.read_alarms()
            print('Alarms:', alarms)
            assert len(alarms) >= 3
            assert country.encode() in alarms
            assert location.encode() in alarms
            assert b'SAAR{flag3}' in alarms

            # TODO read checks - check what is accessible
            assert conn.get(f'user:{username}:name') == username.encode()
            # TODO pub/sub checks?
            # TODO check what is not accessible
            # VULN1 - GET strings but nothing else
            conn2.conn.get(f'user:{username}:flag')
            try:
                conn.conn.get(f'user:{username2}:alarms')
                raise Exception('GET on list possible')
            except redis.exceptions.ResponseError:
                pass
            try:
                conn.conn.get(f'country:{country}:firefighters')
                raise Exception('GET on hash possible')
            except redis.exceptions.ResponseError:
                pass
            try:
                conn.conn.hgetall(f'country:{country}:firefighters')
                raise Exception('HGETALL')
            except redis.exceptions.ResponseError:
                pass
            try:
                conn.conn.execute_command('MONITOR')
                raise Exception('MONITOR')
            except redis.exceptions.ResponseError:
                pass
            try:
                conn.conn.execute_command('KEYS party:*')
                raise Exception('KEYS')
            except redis.exceptions.ResponseError:
                pass
            try:
                conn.conn.execute_command('SCAN 0 MATCH party:*')
                raise Exception('SCAN')
            except redis.exceptions.ResponseError:
                pass


if __name__ == '__main__':
    check_permissions('127.0.0.1' if len(sys.argv) < 2 else sys.argv[1])
