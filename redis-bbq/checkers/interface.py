import random
import sys
import uuid

from gamelib import *
import redis

try:
    from .connectors import RedisConnector, HttpConnector, get_random_connector, modify_location
except ImportError:
    from connectors import RedisConnector, HttpConnector, get_random_connector, modify_location


ORIGINAL_LOLS = {
    5: b'\xe2\xa0\x80\xe2\xa1\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa1\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa1\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa1\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa1\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4\xe2\xa0\xa4',
    6: b'\x1b[0;97;107m \x1b[0m\x1b[0;97;107m \x1b[0m\x1b[0;97;107m \x1b[0m\x1b[0;97;107m \x1b[0m\x1b[0;97;107m \x1b[0m\x1b[0;97;107m \x1b[0m\x1b[0;97;107m \x1b[0m\x1b[0;97;107m \x1b[0m\x1b[0;97;107m',
    None: b'Redis ver. 7.'
}


class RedisBBQInterface(ServiceInterface):
    name = 'RedisBBQ'

    def check_integrity(self, team: Team, tick: int):
        try:
            with HttpConnector(team.ip, 16379) as conn:
                print('> GET /')
                response = conn.http_get('/')
                assert_requests_response(response, 'text/html; charset=utf-8')
                print('> HTTP PING ...')
                conn.ping()
            with RedisConnector(team.ip, 16379) as conn:
                print('> REDIS PING ...')
                conn.ping()
                version, expected_lol = random.choice(list(ORIGINAL_LOLS.items()))
                print(f'> LOLWUT ({version})')
                lol = conn.lolwut(version)
                if not lol.startswith(expected_lol):
                    print('Invalid LOLWUT (received vs ref):')
                    print(lol)
                    print(expected_lol)
                    raise MumbleException('Invalid responses to Redis commands')
                print('Server is genuine.')
        except redis.exceptions.ConnectionError:
            raise OfflineException('Connection error')
        except redis.exceptions.TimeoutError:
            raise OfflineException('Connection timeout error')
        except redis.exceptions.RedisError:
            raise MumbleException('Redis error')

    def store_flags(self, team: Team, tick: int):
        flag1 = self.get_flag(team, tick, 0)
        flag2 = self.get_flag(team, tick, 1)
        flag3 = self.get_flag(team, tick, 2)
        # User 1: Has flag1 in its profile, creates party with flag3 in its location
        user1 = usernames.generate_username()
        pass1 = usernames.generate_password(16, 20)
        # User 2: Guest to the party, adds flag2 as food
        user2 = usernames.generate_username()
        pass2 = usernames.generate_password(16, 20)
        # User 3: Firefighter, with location near to the party's fire, receives flag3
        user3 = usernames.generate_username()
        pass3 = usernames.generate_password(16, 20)
        print(f'User 1: {user1} / {pass1}')
        print(f'User 2: {user2} / {pass2}')
        print(f'User 3: {user3} / {pass3}')

        country = usernames.generate_random_string(12, False)
        location = usernames.generate_random_string(16, False)
        location2 = modify_location(location, 2)
        fire_id = str(uuid.uuid4())
        party_id = str(uuid.uuid4())
        wood = random.randint(10, 40)

        self.store(team, tick, 'users', [user1, pass1, user2, pass2, user3, pass3, country, location, location2, fire_id, party_id])

        try:
            with get_random_connector(team.ip, 16379, team.id + tick) as conn1:
                # Register user1
                conn1.new_user(user1, pass1)
                conn1.auth(user1, pass1)
                conn1.set(f'user:{user1}:dishes', flag1)
                conn1.lpush(f'newest:users', user1)
                # Create party and fire
                conn1.create_party(party_id, f"{user1}'s secret barbecue", [user1], ['Schwenker'])
                conn1.create_fire(fire_id, country, location, flag3, party_id)
                conn1.lpush(f'newest:countries', country)
                conn1.incr(f'fire:{fire_id}:wood', wood)
                print('--------------------')

            with get_random_connector(team.ip, 16379, team.id + tick + 1) as conn2:
                # Register user2
                conn2.new_user(user2, pass2)
                conn2.auth(user2, pass2)
                # Join the party
                conn2.sadd(f'party:{party_id}:guests', user2)
                conn2.sadd(f'party:{party_id}:food', flag2)
                print('--------------------')

            with get_random_connector(team.ip, 16379, team.id + tick + 2) as conn3:
                # Register user3
                conn3.new_user(user3, pass3)
                conn3.auth(user3, pass3)
                # Register FF watch
                ff_loc = json.dumps({'country': country, 'location': location2}).replace(' ', '')
                r = conn3.hsetnx(f'country:{country}:firefighters', user3, ff_loc)
                assert r == 1, 'Could not add watch location'
                conn3.lpush(f'user:{user3}:watch_locations', ff_loc)
                # Check alarms for once
                alarms = conn3.read_alarms()
                assert len(alarms) == 0, 'Alarms not empty after registration'
                print('--------------------')

        except redis.exceptions.ConnectionError:
            raise OfflineException('Connection error')
        except redis.exceptions.TimeoutError:
            raise OfflineException('Connection timeout error')
        except redis.exceptions.RedisError:
            raise MumbleException('Redis error')

    def retrieve_flags(self, team: Team, tick: int):
        flag1 = self.get_flag(team, tick, 0)
        flag2 = self.get_flag(team, tick, 1)
        flag3 = self.get_flag(team, tick, 2)

        try:
            user1, pass1, user2, pass2, user3, pass3, country, location, location2, fire_id, party_id = self.load(team, tick, 'users')
        except:
            raise FlagMissingException('Store never executed')

        try:
            # Check that user and country are still in newest
            with get_random_connector(team.ip, 16379, team.id + tick + 3) as conn0:
                users = conn0.unauth_lrange('newest:users')
                if user1.encode() not in users:
                    raise FlagMissingException(f'User {user1} not among the newest users')
                countries = conn0.unauth_lrange('newest:countries')
                if country.encode() not in countries:
                    raise FlagMissingException(f'Country {country} not among the newest countries')
                fires = conn0.unauth_lrange(f'country:{country}:fires')
                if fire_id.encode() not in fires:
                    raise FlagMissingException(f'Fire {fire_id} not in country {country} fire list')
                print('--------------------')

            # Login as user1 and retrieve profile info
            with get_random_connector(team.ip, 16379, team.id + tick) as conn1:
                conn1.auth(user1, pass1)
                name, dishes, dishes_cooked, watch_locations = conn1.read_profile()
                assert dishes == flag1.encode(), 'Flag1 not found (dishes)'
                # Retrieve party info, check guests and food
                name, organisator, r_fire_id, guests, food = conn1.read_party(party_id)
                assert user1.encode() in name, 'Party name missing'
                assert organisator == user1.encode(), 'Organisator missing'
                assert r_fire_id == fire_id.encode(), 'Fire ID got lost'
                assert user1.encode() in guests, f'Guest {user1} missing'
                assert user2.encode() in guests, f'Guest {user2} missing'
                assert b'Schwenker' in food, 'Food missing'
                if flag2.encode() not in food:
                    raise FlagMissingException('Flag2 not found (food)')
                # Add some more food to trigger exploits again
                conn1.sadd(f'party:{party_id}:food', f'{random.randint(0, 1000)} more Schwenker')
                print('--------------------')

            # Login as user2, add more wood, trigger firealarm
            with get_random_connector(team.ip, 16379, team.id + tick + 1) as conn2:
                conn2.auth(user2, pass2)
                conn2.incr(f'fire:{fire_id}:wood', random.randint(20, 40))
                conn2.firealarm(fire_id)
                print('--------------------')

            # Login as user3, check that firealarm has been delivered
            with get_random_connector(team.ip, 16379, team.id + tick + 2) as conn3:
                conn3.auth(user3, pass3)
                name, dishes, dishes_cooked, watch_locations = conn3.read_profile()
                ff_loc = json.dumps({'country': country, 'location': location2}).replace(' ', '')
                assert ff_loc.encode() in watch_locations, 'Watch location got missing'
                alarms = conn3.read_alarms()
                if country.encode() not in alarms or location.encode() not in alarms or flag3.encode() not in alarms:
                    raise FlagMissingException('Flag3 not found (fire content)')

        except redis.exceptions.ConnectionError:
            raise OfflineException('Connection error')
        except redis.exceptions.TimeoutError:
            raise OfflineException('Connection timeout error')
        except redis.exceptions.RedisError:
            raise MumbleException('Redis error')


if __name__ == '__main__':
    team = Team(1, 'Test', sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1')
    service = RedisBBQInterface(1)

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
