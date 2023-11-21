import unittest
import pwn
from pwnlib.util import fiddling

from messages import TEST_MESSAGES
from transport_crypt import transport_crypt
USE_TRANSPORT_CRYPT = True

BOARD_PORT = 30007
GOOD_SYSID = b"3"
GOOD_USER_RECORD_EMPLOYEE_ID = b"80e0d3254e5841879f3b2cc2949e18c4"
GOOD_USER_RECORD = b"0|A|A|A|" + GOOD_USER_RECORD_EMPLOYEE_ID + b"|coder|30"

class TestBoard(unittest.TestCase):

	##############################
	# Helper functions
	##############################

	def connect(self, verbose=False):
		pwn.context.log_level = "debug" if verbose else "warning"
		self.conn = pwn.remote("127.0.0.1", BOARD_PORT)

	def disconnect(self):
		self.conn.close()

	def sendline_tc(self, by):
		if USE_TRANSPORT_CRYPT:
			self.conn.send(transport_crypt(bytearray(by) + self.conn.newline))
		else:
			self.conn.sendline(by)

	def recvall_tc(self):
		by = self.conn.recvall()
		if USE_TRANSPORT_CRYPT:
			return bytes(transport_crypt(bytearray(by)))
		else:
			return by

	def get_count(self, sysid=GOOD_SYSID, user_record=GOOD_USER_RECORD, verbose=False):
		self.connect(verbose)
		self.sendline_tc(sysid + b"|||" + user_record + b"|||" + b"c")
		result = self.recvall_tc()
		self.disconnect()
		return result

	def put_message(self, message, sysid=GOOD_SYSID, user_record=GOOD_USER_RECORD, verbose=False):
		self.connect(verbose)
		self.sendline_tc(
			sysid + b"|||" + user_record + b"|||" +
			b"p|" + message.encode('utf-8')
		)
		result = self.recvall_tc()
		self.disconnect()
		return result

	def get_message_by_id(self, message_id: str, sysid=GOOD_SYSID, user_record=GOOD_USER_RECORD, verbose=False):
		self.connect(verbose)
		self.sendline_tc(
			sysid + b"|||" + user_record + b"|||" + b"i|" + message_id.encode("utf-8")
		)
		result = self.recvall_tc()
		self.disconnect()
		return result

	def get_message_by_number(self, message_number: int, sysid=GOOD_SYSID, user_record=GOOD_USER_RECORD, verbose=False):
		self.connect(verbose)
		self.sendline_tc(
			sysid + b"|||" + user_record + b"|||" + b"n|" + str(message_number).encode("utf-8")
		)
		result = self.recvall_tc()
		self.disconnect()
		return result

	########

	def get_count_checked(self, sysid=GOOD_SYSID, user_record=GOOD_USER_RECORD, verbose=False):
		result_count = self.get_count(sysid=sysid, user_record=user_record, verbose=verbose)
		assert (result_count[1] == 0x47 and result_count[0] == ord("c"))
		result_count_str = result_count[2:].decode('utf-8')
		result_count_parts = result_count_str.split("|||")
		assert (len(result_count_parts) == 2)
		assert (result_count_parts[0].encode() == user_record)
		count = int(result_count_parts[1].rstrip())
		return count

	def put_message_checked(self, message, sysid=GOOD_SYSID, user_record=GOOD_USER_RECORD, verbose=False):
		result_put = self.put_message(message, sysid=sysid, user_record=user_record, verbose=verbose)
		assert (result_put[1] == 0x47 and result_put[0] == ord("p"))
		result_put_str = result_put[2:].decode('utf-8')
		result_put_parts = result_put_str.split("|||")
		assert (len(result_put_parts) == 2)
		assert (result_put_parts[0].encode() == user_record)
		msg_id = result_put_parts[1].rstrip()
		return msg_id

	def get_message_by_id_checked(self, message_id: str, sysid=GOOD_SYSID, user_record=GOOD_USER_RECORD, verbose=False):
		user_record_parts = user_record.decode('utf-8').split("|")

		result_get = self.get_message_by_id(message_id, verbose=verbose)
		assert (result_get[1] == 0x47 and result_get[0] == ord("i"))
		result_get_str = result_get[2:].decode('utf-8')
		result_get_parts = result_get_str.split("|||")
		assert (len(result_get_parts) == 2)
		assert (result_get_parts[0].encode() == user_record)

		user_and_message = result_get_parts[1]
		user_and_message_parts = user_and_message.split("|")
		assert (user_and_message_parts[0] == user_record_parts[1])
		assert (user_and_message_parts[1] == user_record_parts[2])
		return user_and_message_parts[2].rstrip()

	def get_message_by_number_checked(self, message_number: int, sysid=GOOD_SYSID, user_record=GOOD_USER_RECORD, verbose=False):
		result_get = self.get_message_by_number(
			message_number, sysid=sysid,
			user_record=user_record if user_record is not None else GOOD_USER_RECORD,
			verbose=verbose
		)
		if (result_get[1] == 0x53 and result_get[0] == 0x06): # bad number
			return None

		assert (result_get[1] == 0x47 and result_get[0] == ord("n"))
		result_get_str = result_get[2:].decode('utf-8')
		result_get_parts = result_get_str.split("|||")
		assert (len(result_get_parts) == 2)
		if user_record is not None:
			assert (result_get_parts[0].encode() == user_record)
		user_and_message = result_get_parts[1]

		user_and_message_parts = user_and_message.split("|")
		if user_record is not None:
			user_record_parts = user_record.decode('utf-8').split("|")
			assert (user_and_message_parts[0] == user_record_parts[1])
			assert (user_and_message_parts[1] == user_record_parts[2])
		return user_and_message_parts[2].rstrip()

	def put_and_get(self, message, user_record=GOOD_USER_RECORD, expected=None, verbose=False):
		# get number of messages on the board
		count_before = self.get_count_checked(user_record=user_record, verbose=verbose)

		# put the message
		msg_id = self.put_message_checked(message, user_record=user_record, verbose=verbose)

		# try to retrieve message again
		message_get = self.get_message_by_id_checked(msg_id, verbose=verbose)
		assert ((message if expected is None else expected).rstrip() == message_get)

		# get number of messages on the board again, should be +1 now.
		count_after = self.get_count_checked(user_record=user_record, verbose=verbose)

		assert (count_after == count_before + 1)


	##############################
	# Tests
	##############################

	def test_put_length_0_to_1000(self):
		for mlen in range(0, 1000 + 1):
			# print(f"Testing length {mlen}")
			# generate a random message of length mlen
			message = fiddling.randoms(mlen)

			# put the message
			result = self.put_message_checked(message)

	def test_put_length_1001(self):
		# generate a random message of length 1001
		message = fiddling.randoms(1001)

		# put the message
		result = self.put_message(message)
		# expect error code
		assert (result[1] == 0x53 and result[0] == 0x04)

	def test_get(self):
		message = fiddling.randoms(512)
		self.put_and_get(message)

	def test_bad_sysid(self):
		result = self.get_count(sysid=b"2")
		assert (result[1] == 0x53)

	def test_bug_uint_cast(self):
		record = b"0|Peter|Schmidt|asdf|80e0d3254e5841879f3b2cc2949e18c4|coder|-2" # negative holidays
		expected = b"0|Peter|Schmidt|asdf|80e0d3254e5841879f3b2cc2949e18c4|coder|" + str((1 << 32) - 2).encode('utf-8') # negative holidays
		# print(f"Testing good record: {record}")
		result = self.put_message("foo", user_record=record)
		assert (result[1] == 0x47 and result[0] == ord("p"))
		assert (result[2:].startswith(expected))

	def test_user_records(self):
		records_good = [
			b"0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30",
			b"0|A|A|asdlkfj!@#$%^&*()-+=_\\'\"\t|80e0d3254e5841879f3b2cc2949e18c4|coder|30", # complex password
			b"0|Peter Gerhard|Schmidt|asdlkfj*(#$$%&|80e0d3254e5841879f3b2cc2949e18c4|coder|30", # space
			"0|Peter|Müller|asdf|80e0d3254e5841879f3b2cc2949e18c4|coder|30".encode("utf-8"), # umlaut
			b"0|Peter|Schmidt|asdf|80e0d3254e5841879f3b2cc2949e18c4|coder|0", # no holidays
			# b"0|Peter|Schmidt|asdf|80e0d3254e5841879f3b2cc2949e18c4|coder|-2", # negative holidays
			b"0|Peter|Schmidt|asdf|80e0d3254e5841879f3b2cc2949e18c4|coder|30||foo", # with 1 obj with 1 element
			b"0|Peter|Schmidt|asdf|80e0d3254e5841879f3b2cc2949e18c4|coder|30||foo|bar|baz", # with 1 obj with three elements
			b"0|Peter|Schmidt|asdf|80e0d3254e5841879f3b2cc2949e18c4|coder|30||foo|bar|baz||bar||bar|baz|foo", # with 3 objs
		]
		records_bad = [
			b"0||Schmidt|asdf|80e0d3254e5841879f3b2cc2949e18c4|coder|30", # empty first
			b"0|Peter||asdf|80e0d3254e5841879f3b2cc2949e18c4|coder|30", # empty last
			b"0|Peter|Schmidt||80e0d3254e5841879f3b2cc2949e18c4|coder|30", # empty pass
			b"0|Peter|Schmidt|asdf||coder|30", # empty eid
			b"0|Peter|Schmidt|asdf|80e0d3254e5841879f3b2cc2949e18c4||30", # empty jobdesc
			b"0|||asdf|80e0d3254e5841879f3b2cc2949e18c4|coder|30", # empty first and last (will fail due to |||)
		]
		for record in records_good:
			# print(f"Testing good record: {record}")
			result = self.put_message_checked("foo", user_record=record)
		for record in records_bad:
			# print(f"Testing bad record: {record}")
			result = self.get_count(user_record=record)
			assert (result[1] == 0x53)

	def test_keeping_other_data_records(self):
		# format: data records to send, expected data records in response
		records = [
			(b"30||0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30", ["0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30", "30"]),
			(b"01||0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30", ["0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30", "01"]),
			(b"10|a|b|12|c||0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30", ["0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30", "10|a|b|12|c"]),
			(b"11432423asdf||0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30", ["0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30", "11432423asdf"]),
			(b"10||20||30||0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30", ["0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30", "10", "20", "30"]),
			(b"0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30||10", ["0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30", "10"]),
			(b"0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30||01", ["0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30", "01"]),
			(b"0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30||10|a|b|12|c", ["0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30", "10|a|b|12|c"]),
			(b"11432423asdf||0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30", ["0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30", "11432423asdf"]),
			(b"10||20||0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30||30", ["0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30", "10", "20", "30"]),
		]
		message = "test"
		for record in records:
			# print(f"Testing record: {record}")
			result = self.put_message("foo", user_record=record[0])
			assert (result[1] == 0x47 and result[0] == ord("p"))
			result_str = result[2:].decode("utf-8", errors="ignore")
			outer_parts = result_str.split("|||")
			assert (len(outer_parts) > 0)
			inner_parts = outer_parts[0].split("||")
			for inner_part in inner_parts:
				inner_part = inner_part.encode()
			for expected_data_record in record[1]:
				assert (expected_data_record in inner_parts)
			assert (len(inner_parts) == len(record[1]))

	def test_bad_command(self):
		self.connect()
		self.sendline_tc(
			GOOD_SYSID + b"|||" + GOOD_USER_RECORD + b"|||" + b"b"
		)
		result = self.recvall_tc()
		self.disconnect()
		assert (result[1] == 0x53)

	def test_message_strip(self):
		message_pairs = [
			("ends in space ", "ends in space"),
			("ends in spaces   ", "ends in spaces"),
			("ends in tab\t", "ends in tab"),
			("ends in newline\n", "ends in newline"),
			("ends in newlines\n\n", "ends in newlines"),
			("ends in tabs\t\t\t", "ends in tabs"),
			("ends in mix \t \t  \t", "ends in mix"),
			("ends with dot space. ", "ends with dot space."),
			("  dont strip beginning", "  dont strip beginning"),
			(" \t dont strip beginning", " \t dont strip beginning"),
		]
		for message, expected in message_pairs:
			# print(f"Testing message '{message}', expecting '{expected}'")
			self.put_and_get(message, expected=expected)

	def test_message_contents(self):
		messages_good = [
			"", # empty message
			"Ümläutß",
			"Ending dot.",
			"!@#$@^#@&*^!$(*^#$()_#@_$^#&*@($)!@#(!*({}[][}{}\\\":\":';\"]))<><./?", # some special chars
			"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789=+/", # base64 charset
			"\N{snake}", # emoji
		]
		messages_bad = [
			"Ending pipe|",
		]
		for message in messages_good:
			# print(f"Testing good message {message}")
			self.put_and_get(message)
		for message in messages_bad:
			# print(f"Testing bad message {message}")
			result = self.put_message(message)
			assert (result[1] == 0x53)

	def test_get_by_number(self):
		# put some messages
		no_msg = 10
		messages = []
		for i in range(no_msg):
			message = fiddling.randoms(512)
			messages.append(message)
			result_put = self.put_message_checked(message)

		# get total count
		count = self.get_count_checked()

		# get the messages, make sure all messages we put are still present
		found_ctr = 0
		for message_number in range(count):
			message = self.get_message_by_number_checked(message_number, user_record=None)
			if message is not None and message in messages:
				found_ctr += 1
		assert (found_ctr == no_msg)

	def test_put_many(self):
		no_msg = 10000
		for i in range(no_msg):
			message = fiddling.randoms(512)
			msg_id = self.put_message_checked(message)

		# try to retrieve last message again
		retrieved_message = self.get_message_by_id_checked(msg_id)
		assert (retrieved_message == message)

	def test_get_high_number(self):
		result = self.get_message_by_number(999999999999999)
		assert (result[1] == 0x53)

	def test_test_messages(self):
		for message in TEST_MESSAGES:
			self.put_and_get(message)

if __name__ == '__main__':
	unittest.main()
