#pragma once

#include <inttypes.h>
#include <stddef.h>
#include <sys/types.h>
#include <sys/socket.h>

uint64_t const TRANSPORT_CRYPT_INITIAL_SEED = 0xEA0A8EEA0A8EEA0AULL;

struct transport_crypt_state_t {
	uint64_t seed = TRANSPORT_CRYPT_INITIAL_SEED;
	uint8_t count = 0;
};

ssize_t recv_tc(int sockfd, void* buf, size_t len, int flags);
ssize_t send_tc(int sockfd, void const* buf, size_t len, int flags);
ssize_t recv_tc_state(transport_crypt_state_t* state, int sockfd, void* buf, size_t len, int flags);
ssize_t send_tc_state(transport_crypt_state_t* state, int sockfd, void const* buf, size_t len, int flags);