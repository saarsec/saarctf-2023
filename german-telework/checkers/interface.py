try:
    from telecommunication import telecommunication 
except ImportError:
    from .telecommunication import telecommunication
from gamelib import *
from pwn import remote
import sys
import base64
import re
import random
import binascii

# See the "SampleServiceInterface" from gamelib for a bigger example
# See https://gitlab.saarsec.rocks/saarctf/gamelib/-/blob/master/docs/howto_checkers.md for documentation.


# create a task and check if it tells about the success
def test_task_create(ip):
    try:
        conn = remote(ip, 30000, timeout=TIMEOUT, ssl=True)
    except TimeoutError:
        raise gamelib.MumbleException("Connection timed out")
    try:
        first, last, pw = telecommunication.register_and_login(conn)
        telecommunication.receive_main_menu(conn)
        telecommunication.enter_task_menu(conn)
        answer, task_name, _, _, _, _, _ = telecommunication.create_task(conn)
        assert b"Success" in answer, "Task creation in task creation test failed"
    finally:
        conn.close()


# create a task, complete it and check that both
# creation and completion answer with "successfully"
def test_task_complete(ip):
    try:
        conn = remote(ip, 30000, timeout=TIMEOUT, ssl=True)
    except TimeoutError:
        raise gamelib.MumbleException("Connection timed out")
    try:
        first, last, pw = telecommunication.register_and_login(conn)
        telecommunication.receive_main_menu(conn)
        telecommunication.enter_task_menu(conn)
        answer, task_name, _, _, task_epic, _, _  = telecommunication.create_task(conn)
        assert b"Success" in answer, "Task creation in task completion test failed"
        telecommunication.receive_main_menu(conn)
        telecommunication.enter_task_menu(conn)
        answer = telecommunication.complete_task(conn, task_name, task_epic)
        assert b"Success" in answer, "Task completion in task completion test failed"
    finally:
        conn.close()


# create a task, complete it and check that both
# creation and completion answer with "successfully"
def test_task_details(ip):
    try:
        conn = remote(ip, 30000, timeout=TIMEOUT, ssl=True)
    except TimeoutError:
        raise gamelib.MumbleException("Connection timed out")
    try:
        first, last, pw = telecommunication.register_and_login(conn)
        telecommunication.receive_main_menu(conn)
        telecommunication.enter_task_menu(conn)
        answer, task_name, description, steps, epic, sprint, workhours = telecommunication.create_task(conn)
        assert b"Success" in answer, "Task creation in task details test failed"
        telecommunication.receive_main_menu(conn)
        telecommunication.enter_task_menu(conn)
        answer = telecommunication.check_task_details(conn)
        # the request type
        print(answer)
        assert task_name.encode("utf-8") in answer, "task name worng in task details test"
        assert description.encode("utf-8") in answer, "task description wrong in task details test"
    finally:
        conn.close()


# create task and create it again to make sure this fails
def test_duplicate_task(ip):
    try:
        conn = remote(ip, 30000, timeout=TIMEOUT, ssl=True)
    except TimeoutError:
        raise gamelib.MumbleException("Connection timed out")
    try:
        first, last, pw = telecommunication.register_and_login(conn)
        telecommunication.receive_main_menu(conn)
        telecommunication.enter_task_menu(conn)
        answer, task_name, _, _, _, _, _ = telecommunication.create_task(conn)
        telecommunication.receive_main_menu(conn)
        telecommunication.enter_task_menu(conn)
        answer, task_name, _, _, _, _, _ = telecommunication.create_task(conn, task_name=task_name)
        assert b"error" in answer, "Duplicate task creation was possible in duplicate task test"
    finally:
        conn.close()


# take some holiday
def test_take_holiday(ip):
    try:
        conn = remote(ip, 30000, timeout=TIMEOUT, ssl=True)
    except TimeoutError:
        raise gamelib.MumbleException("Connection timed out")
    try:
        first, last, pw = telecommunication.register_and_login(conn)
        telecommunication.receive_main_menu(conn)
        telecommunication.enter_holiday_menu(conn)
        answer, start_date, end_date, _, _, _ = telecommunication.take_time_off(conn)
        assert b"Success" in answer, "Holiday taking failed in take holiday test"
    finally:
        conn.close()


# check cancel holiday 
def test_cancel_holiday(ip):
    try:
        conn = remote(ip, 30000, timeout=TIMEOUT, ssl=True)
    except TimeoutError:
        raise gamelib.MumbleException("Connection timed out")
    try:
        first, last, pw = telecommunication.register_and_login(conn)
        telecommunication.receive_main_menu(conn)
        telecommunication.enter_holiday_menu(conn)
        answer, start_date, end_date, _, _, _ = telecommunication.take_time_off(conn)
        assert b"Success" in answer, "Holiday taking failed in cancel holiday test"
        telecommunication.enter_holiday_menu(conn)
        answer = telecommunication.cancel_holiday(conn, start_date, end_date)
        print(answer)
        assert b"Success" in answer, "Holiday cancellation failed in cancel holiday test"
    finally:
        conn.close()


# take some holiday
def test_list_holiday(ip):
    try:
        conn = remote(ip, 30000, timeout=TIMEOUT, ssl=True)
    except TimeoutError:
        raise gamelib.MumbleException("Connection timed out")
    try:
        first, last, pw = telecommunication.register_and_login(conn)
        telecommunication.receive_main_menu(conn)
        telecommunication.enter_holiday_menu(conn)
        answer, start_date, end_date, reason, destination, phone  = telecommunication.take_time_off(conn)
        assert b"Success" in answer, "Holiday taking failed in list holiday test"
        telecommunication.enter_holiday_menu(conn)
        answer = telecommunication.check_current_bookings(conn)
        assert reason.encode("utf-8") in answer, "Holiday listing failed, missing reason"
        assert destination.encode("utf-8") in answer, "Holiday listing failed, missing destination"
        assert phone.encode("utf-8") in answer, "Holiday listing failed, missing phone"
    finally:
        conn.close()

# function to store task flag
def store_task_flag_existing(ip, flag, flag_id, first, last, pw):
    try:
        conn = remote(ip, 30000, timeout=TIMEOUT, ssl=True)
    except TimeoutError:
        raise gamelib.MumbleException("Connection timed out")
    try:
        telecommunication.login(conn, first, last, pw)
        telecommunication.receive_main_menu(conn)
        telecommunication.enter_task_menu(conn)
        telecommunication.create_task(conn, description=flag)
        return first, last, pw
    finally:
        conn.close()


# function to store task flag
def store_task_flag(ip, flag, flag_id):
    try:
        conn = remote(ip, 30000, timeout=TIMEOUT, ssl=True)
    except TimeoutError:
        raise gamelib.MumbleException("Connection timed out")
    try:
        first, last, pw = telecommunication.register_and_login_specific(conn, flag_id)
        telecommunication.receive_main_menu(conn)
        telecommunication.enter_task_menu(conn)
        telecommunication.create_task(conn, description=flag)
        return first, last, pw
    finally:
        conn.close()


# function to retrieve task flag
def retrieve_task_flag(ip, firstname, lastname, pw):
    try:
        conn = remote(ip, 30000, timeout=TIMEOUT, ssl=True)
    except TimeoutError:
        raise gamelib.MumbleException("Connection timed out")
    try:
        telecommunication.login(conn, firstname, lastname, pw)
        telecommunication.receive_main_menu(conn)
        telecommunication.enter_task_menu(conn)
        answer = telecommunication.check_task_details(conn)
        return answer
    finally:
        conn.close()


def test_messagecrypt_crypt(ip):
    # create recipient user
    try:
        conn = remote(ip, 30000, timeout=TIMEOUT, ssl=True)
    except TimeoutError:
        raise gamelib.MumbleException("Connection timed out")
    try:
        # register & login
        recipient_first, recipient_last, recipient_pw = telecommunication.register_and_login(conn)
        telecommunication.receive_main_menu(conn)

        # get own employee id
        recipient_eid = telecommunication.get_employee_id(conn, recipient_first, recipient_last)
        assert recipient_eid is not None, "Employee register seems broken (1)."

        telecommunication.receive_main_menu(conn)
    finally:
        conn.close()

    # create sender user & encrypt a message to the recipient
    try:
        conn = remote(ip, 30000, timeout=TIMEOUT, ssl=True)
    except TimeoutError:
        raise gamelib.MumbleException("Connection timed out")
    try:
        # register & login
        _, _, _ = telecommunication.register_and_login(conn)
        telecommunication.receive_main_menu(conn)

        # encrypt
        telecommunication.mc_enter_menu(conn)
        message: str = usernames.generate_name(words=3, sep=" ")
        ciphertext_b64s: str = telecommunication.mc_encrypt_message(conn, recipient_eid, base64.b64encode(message.encode()).decode())
        assert ciphertext_b64s != "", "MC: Received empty ciphertext (1)."
        try:
            decoded = base64.b64decode(ciphertext_b64s)
            assert decoded != message.encode(), "MC: Ciphertext must not be same as the plaintext."
        except binascii.Error:
            raise gamelib.MumbleException("MC: Base64 decode failed")

        telecommunication.receive_main_menu(conn)
    finally:
        conn.close()

    # login as recipient & decrypt
    try:
        conn = remote(ip, 30000, timeout=TIMEOUT, ssl=True)
    except TimeoutError:
        raise gamelib.MumbleException("Connection timed out")
    try:
        # login
        telecommunication.login(conn, recipient_first, recipient_last, recipient_pw)
        telecommunication.receive_main_menu(conn)

        # decrypt
        telecommunication.mc_enter_menu(conn)
        plaintext_bytes: bytes = telecommunication.mc_decrypt_message(conn, ciphertext_b64s)
        tmp = plaintext_bytes.rstrip(b"\00")
        assert message.encode() in plaintext_bytes.rstrip(b"\00"), f"MC: Plaintext does not match original message, found {message.encode()}, required {tmp}"

        telecommunication.receive_main_menu(conn)
    finally:
        conn.close()


def test_board(ip):
    try:
        conn = remote(ip, 30000, timeout=TIMEOUT, ssl=True)
    except TimeoutError:
        raise gamelib.MumbleException("Connection timed out")
    try:
        # register & login
        first, last, pw = telecommunication.register_and_login(conn)
        telecommunication.receive_main_menu(conn)

        # get pre-announcement count
        telecommunication.board_enter_menu(conn)
        count_before = telecommunication.board_get_count(conn)
        telecommunication.receive_main_menu(conn)

        # put an announcement
        telecommunication.board_enter_menu(conn)
        message: str = random.choice(telecommunication.TEST_MESSAGES)
        message_id = telecommunication.board_put(conn, message)
        telecommunication.receive_main_menu(conn)

        # get post-announcement count
        telecommunication.board_enter_menu(conn)
        count_after = telecommunication.board_get_count(conn)
        telecommunication.receive_main_menu(conn)

        if (count_after - count_before == 0):
            raise gamelib.MumbleException("Board: Count did not increment when I posted my announcement.")

        if (count_after - count_before == 1):
            # retrieve announcement back (via number)
            telecommunication.board_enter_menu(conn)
            resp: dict[str, str] = telecommunication.board_get_message_by_number(conn, count_after - 1)
            assert resp["message"] == message, "Board: Could not retrieve my own announcement message by number."
            assert resp["first"] == first, "Board: The announcement did not have my first name on it."
            assert resp["last"] == last, "Board: The announcement did not have my last name on it."
            telecommunication.receive_main_menu(conn)

        # retrieve announcement back (via ID)
        telecommunication.board_enter_menu(conn)
        resp: dict[str, str] = telecommunication.board_get_message_by_id(conn, message_id)
        assert resp["message"] == message, "Board: Could not retrieve my own announcement message by ID."
        assert resp["first"] == first, "Board: The announcement did not have my first name on it."
        assert resp["last"] == last, "Board: The announcement did not have my last name on it."
        telecommunication.receive_main_menu(conn)
    finally:
        conn.close()


def store_flag_mc_board(team, tick: int, flag: str, interface):
    try:
        conn = remote(team.ip, 30000, timeout=TIMEOUT, ssl=True)
    except TimeoutError:
        raise gamelib.MumbleException("Connection timed out")
    try:
        # register & login
        first, last, pw = telecommunication.register_and_login(conn)
        telecommunication.receive_main_menu(conn)

        # get own employee id
        eid = telecommunication.get_employee_id(conn, first, last)
        assert eid is not None, "Employee register seems broken (2)."
        telecommunication.receive_main_menu(conn)

        # encrypt
        telecommunication.mc_enter_menu(conn)
        message: str = f"Here you go: {flag}"
        ciphertext_b64s: str = telecommunication.mc_encrypt_message(conn, eid, base64.b64encode(message.encode()).decode())
        assert ciphertext_b64s != "", "MC: Received empty ciphertext (2)."
        telecommunication.receive_main_menu(conn)

        # put an announcement
        telecommunication.board_enter_menu(conn)
        message: str = usernames.generate_name(words=3, sep=" ")
        message_id = telecommunication.board_put(conn, f"Note to self: {ciphertext_b64s}")
        telecommunication.receive_main_menu(conn)

        # store some metadata to make the check easier
        interface.store(team, tick, "state", [first, last, pw, ciphertext_b64s, eid, message_id])
    finally:
        conn.close()


def retrieve_flag_mc_board(team, tick: int, flag: str, interface):
    try:
        conn = remote(team.ip, 30000, timeout=TIMEOUT, ssl=True)
    except TimeoutError:
        raise gamelib.MumbleException("Connection timed out")
    try:
        # load state
        state = interface.load(team, tick, "state")
        if state is None:
            raise FlagMissingException("Flag not found (likely not stored last time).")
        first, last, pw, ciphertext_b64s, eid, message_id = state
        expected: str = f"Note to self: {ciphertext_b64s}".strip()

        # login
        telecommunication.login(conn, first, last, pw)
        telecommunication.receive_main_menu(conn)

        # retrieve announcements and make sure the response contains the encrypted flag
        telecommunication.board_enter_menu(conn)
        resp: dict[str, str] = telecommunication.board_get_message_by_id(conn, message_id)
        if expected not in resp["message"]:
            raise FlagMissingException("Board: Flag not found")

        telecommunication.receive_main_menu(conn)

        # decrypt
        telecommunication.mc_enter_menu(conn)
        plaintext_bytes: bytes = telecommunication.mc_decrypt_message(conn, ciphertext_b64s)
        if flag.encode() not in plaintext_bytes.rstrip(b"\00"):
            raise FlagMissingException("MC: Flag could not be decrypted")
        telecommunication.receive_main_menu(conn)
    finally:
        conn.close()


class TeleworkServiceInterface(ServiceInterface):
    name = 'Telework'
    flag_id_types = ['username']


    def check_integrity(self, team: Team, tick: int):
        # task tests
        print("Test create task...")
        test_task_create(team.ip)
        print("Success!")
        print("Test complete task...")
        test_task_complete(team.ip)
        print("Success!")
        print("Test task details...")
        test_task_details(team.ip)
        print("Success!")
        print("Test duplicate tasks...")
        test_duplicate_task(team.ip)
        print("Success!")
        # holiday tests
        print("Test take holiday...")
        test_take_holiday(team.ip)
        print("Success!")
        print("Test cancel holiday...")
        test_cancel_holiday(team.ip)
        print("Success!")
        print("Test list holiday...")
        test_list_holiday(team.ip)
        print("Success!")
        # mc tests
        test_messagecrypt_crypt(team.ip)
        # board tests
        test_board(team.ip)

    def store_flags(self, team: Team, tick: int):
        # task flag is flag 0
        # it also requires a flag id
        flag0 = self.get_flag(team, tick, 0)
        flag0_id = self.get_flag_id(team, tick, 0)
        # this is relevant for the multiple times thing
        try:
            persistent_info = self.load(team, tick, flag0_id)
            firstname, lastname, pw = persistent_info
            store_task_flag_existing(team.ip, flag0, flag0_id, firstname, lastname, pw)
            self.store(team, tick, flag0_id, [firstname, lastname, pw])
        except Exception as e: 
            firstname, lastname, pw = store_task_flag(team.ip, flag0, flag0_id)
            self.store(team, tick, flag0_id, [firstname, lastname, pw])
        print(f"Flagid: {flag0_id}, firstname: {firstname}")

        # crypto stuff is flag 1
        flag1 = self.get_flag(team, tick, 1)
        store_flag_mc_board(team, tick, flag1, self)


    def retrieve_flags(self, team: Team, tick: int):
        flag0 = self.get_flag(team, tick, 0)
        flag0_id = self.get_flag_id(team, tick, 0)

        persistent_info = self.load(team, tick, flag0_id)
        if persistent_info is None:
            raise FlagMissingException("Flag not found (likely not stored last time).")
        firstname, lastname, pw = persistent_info

        answer = retrieve_task_flag(team.ip, firstname, lastname, pw).decode("utf-8")

        if flag0 not in answer:
            # verbose error logging is always a good idea
            print('GOT task info:', answer)
            # flag not found? Raise FlagMissingException
            raise FlagMissingException('Task flag not found')

        flag1 = self.get_flag(team, tick, 1)
        # flag check happens in retrieve_flag_mc_board
        retrieve_flag_mc_board(team, tick, flag1, self)


if __name__ == '__main__':
    # USAGE: python3 interface.py                      # test against localhost
    # USAGE: python3 interface.py 1.2.3.4              # test against IP
    # USAGE: python3 interface.py 1.2.3.4 retrieve     # retrieve last 10 ticks (for exploits relying on checker interaction)
    # (or use gamelib/run-checkers to test against docker container)
    team = Team(1, 'TestTeam', sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1')
    service = TeleworkServiceInterface(1)

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
