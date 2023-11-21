#pragma once

#include <cstdio>
#include <cstdlib>
#include <cinttypes>

#include <array>

#define MAGENTA_BLOCK_SZ_BITS (128)
#define MAGENTA_BLOCK_SZ_BYTES (MAGENTA_BLOCK_SZ_BITS / 8)

using MAGENTA_state_t = std::array<uint8_t, MAGENTA_BLOCK_SZ_BYTES>;
using MAGENTA_half_state_t = std::array<uint8_t, (MAGENTA_BLOCK_SZ_BYTES / 2)>;

using MAGENTA_key_t = std::array<uint8_t, MAGENTA_BLOCK_SZ_BYTES>;

class MAGENTA {
private:
	std::array<uint8_t, 256> f {};

	template <typename arr_t> arr_t sxor(arr_t const& a, arr_t const& b);
	MAGENTA_state_t concat(MAGENTA_half_state_t const& a, MAGENTA_half_state_t const& b);
	MAGENTA_state_t swap_halves(MAGENTA_state_t const& x);

	// === CIPHER CIPHER ======== CYBER CYBER ========= CYPHER CYPHER ===
	uint8_t A(uint8_t x, uint8_t y);
	uint16_t PE(uint8_t x, uint8_t y);
	MAGENTA_state_t pi(MAGENTA_state_t const& x);
	MAGENTA_state_t T(MAGENTA_state_t const& w);
	MAGENTA_state_t S(MAGENTA_state_t const& x);
	MAGENTA_state_t C(size_t n, MAGENTA_state_t const& w);
	MAGENTA_half_state_t SK(MAGENTA_key_t const& key, size_t n);
	MAGENTA_half_state_t F(MAGENTA_half_state_t const& X2, MAGENTA_half_state_t const& SKn);
	MAGENTA_state_t rnd(size_t n, MAGENTA_state_t const& X, MAGENTA_half_state_t const& SKn);

public:
	MAGENTA(void);
	MAGENTA_state_t encrypt(MAGENTA_state_t const& x, MAGENTA_key_t const& key);
	MAGENTA_state_t decrypt(MAGENTA_state_t const& x, MAGENTA_key_t const& key);
};