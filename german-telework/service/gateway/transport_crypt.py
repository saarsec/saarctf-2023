TRANSPORT_CRYPT_INITIAL_SEED = 0xEA0A8EEA0A8EEA0A
U64MASK = 0xffffffffffffffff

def _transport_crypt_keystream(seed: int) -> int:
	result = seed & U64MASK
	result ^= result << 13 & U64MASK
	result ^= result >> 7 & U64MASK
	result ^= result << 17 & U64MASK
	return result & U64MASK

class TransportCryptState:
	def __init__(self) -> None:
		self.seed: int = TRANSPORT_CRYPT_INITIAL_SEED
		self.count: int = 0

	def _transport_crypt_get_key_byte(self) -> int:
		if self.count == 16:
			self.count = 0
			self.seed = _transport_crypt_keystream(self.seed)
		byte = (self.seed >> self.count) & 0xff
		self.count += 1
		return byte

	def transport_crypt(self, buf: bytearray) -> bytearray:
		for i in range(len(buf)):
			buf[i] ^= self._transport_crypt_get_key_byte()
		return buf

def transport_crypt(buf: bytearray) -> bytearray:
	state = TransportCryptState()
	buf = state.transport_crypt(buf)
	return buf