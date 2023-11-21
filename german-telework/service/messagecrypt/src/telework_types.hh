#pragma once

#include <inttypes.h>
#include <string>
#include <stdexcept>
#include <optional>


struct EmployeeID {
	uint64_t upper;
	uint64_t lower;
	EmployeeID(uint64_t upper, uint64_t lower);
	EmployeeID(std::string const& uuid);
	EmployeeID();
	std::string str() const;
	bool operator==(EmployeeID const& other) const;
};

template <>
struct std::hash<EmployeeID> {
	size_t operator()(EmployeeID const& eid) const {
		return (hash<uint64_t>()(eid.upper) ^ (hash<uint64_t>()(eid.lower) << 1)) >> 1;
	}
};

typedef struct EmployeeID employee_id_t;


struct telework_user_t {
	std::string firstname;
	std::string lastname;
	std::string password;
	employee_id_t employee_id;
	std::string job_desc;
	uint32_t holidays_left;
	std::string remainder;

	std::string serialize() const;
};


typedef struct {
	employee_id_t employee_id_recipient;
	std::string plaintext_b64;
} command_param_enc_t;

typedef struct {
	std::string ciphertext_b64;
} command_param_dec_t;

typedef struct {
	std::string action_id;
	std::optional<command_param_enc_t> command_param_enc;
	std::optional<command_param_dec_t> command_param_dec;
} command_t;