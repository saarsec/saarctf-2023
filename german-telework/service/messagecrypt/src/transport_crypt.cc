#include "transport_crypt.hh"

uint64_t transport_crypt_keystream(uint64_t seed) {
	uint64_t result = seed;
	result ^= result << 13;
	result ^= result >> 7;
	result ^= result << 17;
	return result;
}

uint8_t transport_crypt_get_key_byte(transport_crypt_state_t* state) {
	if (state->count == 16) {
		state->count = 0;
		state->seed = transport_crypt_keystream(state->seed);
	}
	return (state->seed >> (state->count)++);
}

void transport_crypt_state(transport_crypt_state_t* state, uint8_t* buf, size_t n) {
	for (size_t i = 0; i < n; i++) {
		uint8_t key_byte = transport_crypt_get_key_byte(state);
		buf[i] ^= key_byte;
	}
}

ssize_t recv_tc_state(transport_crypt_state_t* state, int sockfd, void* buf, size_t len, int flags) {
	ssize_t bytes_recvd = recv(sockfd, buf, len, flags);
	if (bytes_recvd > 0) {
		transport_crypt_state(state, (uint8_t*)buf, bytes_recvd);
	}
	return bytes_recvd;
}

ssize_t recv_tc(int sockfd, void* buf, size_t len, int flags) {
	transport_crypt_state_t state;
	return recv_tc_state(&state, sockfd, buf, len, flags);
}

ssize_t send_tc_state(transport_crypt_state_t* state, int sockfd, void const* buf, size_t len, int flags) {
	transport_crypt_state(state, (uint8_t*)buf, len);
	return send(sockfd, buf, len, flags);
}

ssize_t send_tc(int sockfd, void const* buf, size_t len, int flags) {
	transport_crypt_state_t state;
	return send_tc_state(&state, sockfd, buf, len, flags);
}