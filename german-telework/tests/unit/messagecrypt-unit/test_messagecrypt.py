import unittest
import base64
import pwn
from pwnlib.util import fiddling

from transport_crypt import transport_crypt
USE_TRANSPORT_CRYPT = True

MESSAGECRYPT_PORT = 30005
GOOD_SYSID = b"2"
GOOD_USER_RECORD_EMPLOYEE_ID = b"80e0d3254e5841879f3b2cc2949e18c4"
GOOD_USER_RECORD = b"0|A|A|A|" + GOOD_USER_RECORD_EMPLOYEE_ID + b"|coder|30"

class TestMessagecrypt(unittest.TestCase):

	##############################
	# Helper functions
	##############################

	def connect(self, verbose=False):
		pwn.context.log_level = "debug" if verbose else "warning"
		self.conn = pwn.remote("127.0.0.1", MESSAGECRYPT_PORT)

	def disconnect(self):
		self.conn.close()

	def sendline_tc(self, by):
		if USE_TRANSPORT_CRYPT:
			tmp = bytearray(by) + b"\n"
			self.conn.send(transport_crypt(tmp))
		else:
			self.conn.sendline(by)

	def recvall_tc(self):
		by = self.conn.recvall()
		if USE_TRANSPORT_CRYPT:
			return bytes(transport_crypt(bytearray(by)))
		else:
			return by

	def encrypt(self, plaintext_str, recipient=GOOD_USER_RECORD_EMPLOYEE_ID, sysid=GOOD_SYSID, user_record=GOOD_USER_RECORD, verbose=False):
		plaintext_b64 = base64.b64encode(plaintext_str.encode("utf-8"))
		self.connect(verbose)
		self.sendline_tc(
			sysid + b"|||" + user_record + b"|||" +
			b"e|" + recipient + b"|" + plaintext_b64
		)
		result = self.recvall_tc()
		self.disconnect()
		return result

	def decrypt(self, ciphertext_b64, sysid=GOOD_SYSID, user_record=GOOD_USER_RECORD, verbose=False):
		self.connect(verbose)
		self.sendline_tc(
			sysid + b"|||" + user_record + b"|||" + b"d|" + ciphertext_b64
		)
		result = self.recvall_tc()
		self.disconnect()
		return result

	def encrypt_and_decrypt(self, message_str, user_record=GOOD_USER_RECORD, verbose=False):
		# encrypt the message
		result_enc = self.encrypt(message_str, user_record=user_record, verbose=verbose)
		assert (result_enc[1] == 0x47 and result_enc[0] == ord("e"))
		assert (result_enc[2:2 + len(user_record) + 3] == user_record + b"|||")
		ciphertext = result_enc[2 + len(user_record) + 3:-1]

		# try to decrypt message again
		result_dec = self.decrypt(ciphertext, user_record=user_record, verbose=verbose)
		assert (result_dec[1] == 0x47 and result_dec[0] == ord("d"))
		assert (result_dec[2:2 + len(user_record)] == user_record)
		assert (message_str.encode("utf-8") in base64.b64decode(result_dec[2 + len(user_record):]))

	##############################
	# Tests
	##############################

	def test_length_1_to_512(self):
		for mlen in range(1, 512 + 1):
			# print(f"Testing length {mlen}")
			# generate a random message of length mlen
			message = fiddling.randoms(mlen)
			# encrypt and decrypt the message
			result = self.encrypt_and_decrypt(message)

	def test_length_513(self):
		# generate a random message of length 513
		message = fiddling.randoms(513)
		# encrypt the message
		result = self.encrypt(message)
		# expect error code
		assert (result[1] == 0x53)

	def test_encrypt_to_someone_else(self):
		sender_eid = b"eb36a131f59b42c58442e10920bcd049"
		sender_user_record = b"0|Alice|Meier|passwd|" + sender_eid + b"|coder|30"
		recipient_eid = b"2bf75c6df764422c96191d1cd820ea16"
		recipient_user_record = b"0|Peter|Schmidt|hypersecure|" + recipient_eid + b"|coder|30"
		message = fiddling.randoms(256)
		# print(f"from: {sender_eid} to: {recipient_eid} message: {message}")

		# encrypt the message
		result_enc = self.encrypt(message, recipient=recipient_eid, user_record=sender_user_record)
		assert (result_enc[1] == 0x47 and result_enc[0] == ord("e"))
		assert (result_enc[2:2 + len(sender_user_record) + 3] == sender_user_record + b"|||")
		ciphertext = result_enc[2 + len(sender_user_record) + 3:-1]

		# decrypt the message
		result_dec = self.decrypt(ciphertext, user_record=recipient_user_record)
		assert (result_dec[1] == 0x47 and result_dec[0] == ord("d"))
		assert (result_dec[2:2 + len(recipient_user_record)] == recipient_user_record)
		assert (message.encode('utf-8') in base64.b64decode(result_dec[2 + len(recipient_user_record):]))

	def test_bad_sysid(self):
		result = self.encrypt("test", sysid=b"1")
		assert (result[1] == 0x53)

	def test_user_records(self):
		records_good = [
			b"0|A|A|A|80e0d3254e5841879f3b2cc2949e18c4|coder|30",
			b"0|A|A|asdlkfj!@#$%^&*()-+=_\\'\"\t|80e0d3254e5841879f3b2cc2949e18c4|coder|30", # complex password
			b"0|Peter Gerhard|Schmidt|asdlkfj*(#$$%&|80e0d3254e5841879f3b2cc2949e18c4|coder|30", # space
			"0|Peter|Müller|asdf|80e0d3254e5841879f3b2cc2949e18c4|coder|30".encode("utf-8"), # umlaut
			b"0|Peter|Schmidt|asdf|80e0d3254e5841879f3b2cc2949e18c4|coder|0", # no holidays
			b"0|Peter|Schmidt|asdf|80e0d3254e5841879f3b2cc2949e18c4|coder|-2", # negative holidays
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
			b"0|Peter|Schmidt|asdf|80e0d3254e5841879f3b2cc2949e18c4|coder|", # empty holidays
			b"0|Peter|Schmidt|asdf|-80e0d3254e5841879f3b2cc2949e18c4|coder|", # negative eid
			b"0|||asdf|80e0d3254e5841879f3b2cc2949e18c4|coder|30", # empty first and last (will fail due to |||)
		]
		message = "test"
		for record in records_good:
			# print(f"Testing good record: {record}")
			result = self.encrypt(message, user_record=record)
			assert (result[1] == 0x47)
		for record in records_bad:
			# print(f"Testing bad record: {record}")
			result = self.encrypt(message, user_record=record)
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
			result = self.encrypt(message, user_record=record[0])
			assert (result[1] == 0x47)
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
		messages = [
			"ends in space ",
			"ends in spaces   ",
			"ends in tab\t",
			"ends in newline\n",
			"ends in newlines\n\n",
			"ends in tabs\t\t\t",
			"ends in mix \t \t  \t",
			"ends with dot space. ",
			"  dont strip beginning",
			" \t dont strip beginning",
		]
		for message in messages:
			# print(f"Testing message {message}")
			self.encrypt_and_decrypt(message)

	def test_message_contents(self):
		messages_good = [
			"test",
			"Ümläutß",
			"Ending dot.",
			"!@#$@^#@&*^!$(*^#$()_#@_$^#&*@($)!@#(!*({}[][}{}\\\":\":';\"]))<><./?", # some special chars
			"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789=+/", # base64 charset
			"\N{snake}", # emoji
			"Ending pipe|",
			"\x00\x01\x00\x01\x00\xff"
		]
		messages_bad = [
			"", # empty message
		]
		for message in messages_good:
			# print(f"Testing good message {message}")
			self.encrypt_and_decrypt(message)
		for message in messages_bad:
			# print(f"Testing bad message {message}")
			result = self.encrypt(message)
			assert (result[1] == 0x53)

if __name__ == '__main__':
	unittest.main()
