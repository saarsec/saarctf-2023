#include "magenta.hh"


template <typename arr_t>
arr_t MAGENTA::sxor(arr_t const& a, arr_t const& b) {
	arr_t out;
	for (size_t i = 0; i < a.size(); i++) {
		out[i] = a[i] ^ b[i];
	}
	return out;
}

MAGENTA_state_t MAGENTA::concat(MAGENTA_half_state_t const& a, MAGENTA_half_state_t const& b) {
	return {
		a[0], a[1], a[2], a[3],
		a[4], a[5], a[6], a[7],
		b[0], b[1], b[2], b[3],
		b[4], b[5], b[6], b[7],
	};
}

MAGENTA_state_t MAGENTA::swap_halves(MAGENTA_state_t const& x) {
	return {
		x[ 8], x[ 9], x[10], x[11],
		x[12], x[13], x[14], x[15],
		x[ 0], x[ 1], x[ 2], x[ 3],
		x[ 4], x[ 5], x[ 6], x[ 7],
	};
}

// === CIPHER CIPHER ======== CYBER CYBER ========= CYPHER CYPHER ===

MAGENTA::MAGENTA(void) {
	f[0] = 1;
	uint16_t current = f[0];
	for (size_t i = 1; i < 255; i++) {
		current <<= 1;
		if (current & 0x100) {
			current ^= 101;
		}
		f[i] = current;
	}
	f[255] = 0;
}

uint8_t MAGENTA::A(uint8_t x, uint8_t y) {
	return f[x ^ f[y]];
}

uint16_t MAGENTA::PE(uint8_t x, uint8_t y) {
	return (A(x, y) << 8) | A(y, x);
}

MAGENTA_state_t MAGENTA::pi(MAGENTA_state_t const& x) {
	std::array<uint16_t, 8> tmp;
	for (size_t i = 0; i < 8; i++) {
		tmp[i] = PE(x[i], x[8+i]);
	}
	MAGENTA_state_t out;
	for (size_t i = 0; i < 8; i += 1) {
		out[2 * i] = tmp[i] >> 8;
		out[2 * i + 1] = tmp[i] & 0xff;
	}
	return out;
}

MAGENTA_state_t MAGENTA::T(MAGENTA_state_t const& w) {
	return pi(pi(pi(pi(w))));
}

MAGENTA_state_t MAGENTA::S(MAGENTA_state_t const& x) {
	return {
		x[ 0], x[ 2], x[ 4], x[ 6],
		x[ 8], x[10], x[12], x[14],
		x[ 1], x[ 3], x[ 5], x[ 7],
		x[ 9], x[11], x[13], x[15],
	};
}

MAGENTA_state_t MAGENTA::C(size_t n, MAGENTA_state_t const& w) {
	if (n == 1) {
		return T(w);
	}
	return T(sxor(w, S(C(n-1, w))));
}

MAGENTA_half_state_t MAGENTA::SK(MAGENTA_key_t const& key, size_t n) {
	if (n == 3 || n == 4) {
		return {
			key[ 8], key[ 9], key[10], key[11],
			key[12], key[13], key[14], key[15],
		};
	}
	return {
		key[0], key[1], key[2], key[3],
		key[4], key[5], key[6], key[7],
	};
}

MAGENTA_half_state_t MAGENTA::F(MAGENTA_half_state_t const& X2, MAGENTA_half_state_t const& SKn) {
	MAGENTA_state_t in = concat(X2, SKn);
	MAGENTA_state_t out = S(C(3, in));
	return {
		out[0], out[1], out[2], out[3],
		out[4], out[5], out[6], out[7],
	};
}

MAGENTA_state_t MAGENTA::rnd(size_t n, MAGENTA_state_t const& X, MAGENTA_half_state_t const& SKn) {
	MAGENTA_half_state_t X1 {
		X[0], X[1], X[2], X[3],
		X[4], X[5], X[6], X[7],
	};
	MAGENTA_half_state_t X2 {
		X[ 8], X[ 9], X[10], X[11],
		X[12], X[13], X[14], X[15],
	};

	MAGENTA_half_state_t tmp = sxor(X1, F(X2, SKn));
	
	return concat(X2, tmp);
}

MAGENTA_state_t MAGENTA::encrypt(MAGENTA_state_t const& x, MAGENTA_key_t const& key) {
	MAGENTA_state_t state = x;
	for (size_t i = 1; i <= 6; i++) {
		state = rnd(i, state, SK(key, i));
	}
	return state;
}

MAGENTA_state_t MAGENTA::decrypt(MAGENTA_state_t const& x, MAGENTA_key_t const& key) {
	MAGENTA_state_t state = swap_halves(x);
	size_t i = 1;
	do {
		state = rnd(i, state, SK(key, i));
	} while (i++ <= 5);
	return swap_halves(state);
}