#include "conn_handler.hh"
#include "base64.hh"
#include "magenta.hh"

using std::optional;
using std::string;
using std::vector;

MAGENTA magenta;
Keystore<employee_id_t, MAGENTA_key_t> keystore;

#define CHUNK_SIZE 512

vector<string> str_split(string const& in, string const& delim) {
	vector<string> result;
	size_t pos_start = 0;
	size_t pos_match = in.find(delim);
	while (pos_match != string::npos) {
		result.push_back(in.substr(pos_start, pos_match - pos_start));
		pos_start = pos_match + delim.size();
		pos_match = in.find(delim, pos_start);
	}
	result.push_back(in.substr(pos_start, pos_match - pos_start));
	return result;
}

void str_rtrim(string& str) {
	str.erase(
		std::find_if(
			str.rbegin(), str.rend(),
			[](unsigned char ch) {
				return !std::isspace(ch);
			}
		).base(), str.end()
	);
}

optional<telework_user_t> parse_telework_data(string telework_data_serialized) {
	telework_user_t user;

	vector<string> data_parts = str_split(telework_data_serialized, "||");
	string user_record = "";
	string remainder = "";
	for (string const& part : data_parts) {
		if (user_record == "" && part.length() >= 2 && part.substr(0, 2) == "0|")  {
			user_record = part;
		} else {
			user.remainder += "||" + part;
		}
	}
	if (user_record == "") {
		return std::nullopt;
	}

	vector<string> user_parts = str_split(user_record, "|");
	if (user_parts.size() != 7 || user_parts[0] != "0") {
		return std::nullopt;
	}
	user.firstname = user_parts[1];
	user.lastname = user_parts[2];
	user.password = user_parts[3];
	user.job_desc = user_parts[5];

	try {
		user.employee_id = EmployeeID(user_parts[4]);
		user.holidays_left = static_cast<uint32_t>(stoul(user_parts[6]));
	} catch (std::invalid_argument& ex) {
		return std::nullopt;
	} catch (std::out_of_range& ex) {
		return std::nullopt;
	}
	return { user };
}

optional<command_t> parse_command(string command_serialized) {
	vector<string> command_parts = str_split(command_serialized, "|");
	string const& action_id = command_parts[0];
	if (action_id == "e") {
		if (command_parts.size() != 3) {
			return std::nullopt;
		}
		command_t command = {
			.action_id = action_id,
			.command_param_enc = {{
				.plaintext_b64 = command_parts[2]
			}}
		};
		try {
			command.command_param_enc->employee_id_recipient = EmployeeID(command_parts[1]);
		} catch (std::invalid_argument& ex) {
			return std::nullopt;
		} catch (std::out_of_range& ex) {
			return std::nullopt;
		}
		return { command };
	} else if (action_id == "d") {
		if (command_parts.size() != 2) {
			return std::nullopt;
		}
		command_t command = {
			.action_id = action_id,
			.command_param_dec = {{
				.ciphertext_b64 = command_parts[1]
			}}
		};
		return { command };
	}
	return std::nullopt;
}

void* conn_handler(void* param) {
	int connected_socket = *((int*)param);
	uint16_t error_code = 0;
	transport_crypt_state_t tc_state_send;

	{
		std::string received_data;
		transport_crypt_state_t tc_state_recv;
		for (size_t offset = 0;;) {
			received_data.resize(offset + CHUNK_SIZE);
			ssize_t received_bytes = recv_tc_state(
				&tc_state_recv,
				connected_socket,
				(uint8_t*)received_data.data() + offset,
				CHUNK_SIZE,
				0
			);
			if (received_bytes == -1) {
				goto end_thread;
			}
			offset += received_bytes;
			if ((received_bytes < CHUNK_SIZE) || (offset > 0 && received_data.back() == '\n')) {
				received_data.resize(offset);
				break;
			}
		}
		
		str_rtrim(received_data);

		vector<string> recvd_parts = str_split(received_data, "|||");
		if (recvd_parts.size() != 3) {
			error_code = 0x5301;
			goto send_error;
		}
		string const& recvd_subsystem = recvd_parts[0];
		string const& recvd_data = recvd_parts[1];
		string const& recvd_command = recvd_parts[2];
		
		if (recvd_subsystem != "2") {
			error_code = 0x5302;
			goto send_error;
		}

		optional<telework_user_t> opt_user = parse_telework_data(recvd_data);
		if (!opt_user.has_value()) {
			error_code = 0x5303;
			goto send_error;
		}
		telework_user_t const& user = *opt_user;
	
		optional<command_t> opt_command = parse_command(recvd_command);
		if (!opt_command.has_value()) {
			error_code = 0x5304;
			goto send_error;
		}
		command_t const& command = *opt_command;
		
		if (command.action_id == "e") {
			string plaintext_bytes;
			if (command.command_param_enc->plaintext_b64.size() == 0) {
				error_code = 0x5305;
				goto send_error;
			}
			Base64::Decode(command.command_param_enc->plaintext_b64, plaintext_bytes);
			size_t plaintext_len = plaintext_bytes.size();
			if (plaintext_len <= 0 || plaintext_len > 512) {
				error_code = 0x5306;
				goto send_error;
			}
			
			error_code = 0x4700 | command.action_id[0];
			send_tc_state(
				&tc_state_send, connected_socket, &error_code, sizeof(error_code), 0
			);

			string user_resp = user.serialize() + "|||";
			send_tc_state(
				&tc_state_send, connected_socket,
				user_resp.data(), user_resp.size() * sizeof(user_resp.data()[0]), 0
			);

			size_t ciphertext_len = (plaintext_len % MAGENTA_BLOCK_SZ_BYTES == 0)
				? plaintext_len
				: plaintext_len + MAGENTA_BLOCK_SZ_BYTES - (plaintext_len % MAGENTA_BLOCK_SZ_BYTES);
			string ciphertext_bytes;
			ciphertext_bytes.resize(ciphertext_len);
			for (size_t offset = 0; offset < plaintext_len; offset += MAGENTA_BLOCK_SZ_BYTES) {
				MAGENTA_state_t state_in;
				std::copy(
					(uint8_t*)plaintext_bytes.data() + offset,
					(uint8_t*)plaintext_bytes.data() + offset + MAGENTA_BLOCK_SZ_BYTES,
					state_in.begin()
				);
				MAGENTA_state_t state_out = magenta.encrypt(
					state_in,
					keystore.get_key(command.command_param_enc->employee_id_recipient)
				);
				std::copy(
					state_out.begin(),
					state_out.end(),
					(uint8_t*)ciphertext_bytes.data() + offset
				);
			}
			string ciphertext_b64 = Base64::Encode(ciphertext_bytes);
			if (ciphertext_b64.size() > 0) {
				send_tc_state(
					&tc_state_send,
					connected_socket,
					ciphertext_b64.data(),
					ciphertext_b64.size() * sizeof(ciphertext_b64.data()[0]),
					0
				);
			}
		} else if (command.action_id == "d") {
			string ciphertext_bytes;
			Base64::Decode(command.command_param_dec->ciphertext_b64, ciphertext_bytes);
			size_t ciphertext_len = ciphertext_bytes.size();
			if (
				ciphertext_len <= 0
				|| ciphertext_len > 512
				|| ciphertext_len % MAGENTA_BLOCK_SZ_BYTES != 0
			) {
				error_code = 0x5307;
				goto send_error;
			}

			error_code = 0x4700 | command.action_id[0];
			send_tc_state(
				&tc_state_send, connected_socket, &error_code, sizeof(error_code), 0
			);

			string user_resp = user.serialize() + "|||";
			send_tc_state(
				&tc_state_send, connected_socket,
				user_resp.data(), user_resp.size() * sizeof(user_resp.data()[0]), 0
			);
			
			size_t plaintext_len = (ciphertext_len % MAGENTA_BLOCK_SZ_BYTES == 0)
				? ciphertext_len
				: ciphertext_len + MAGENTA_BLOCK_SZ_BYTES - (ciphertext_len % MAGENTA_BLOCK_SZ_BYTES);
			string plaintext_bytes;
			plaintext_bytes.resize(plaintext_len);
			for (size_t offset = 0; offset < ciphertext_len; offset += MAGENTA_BLOCK_SZ_BYTES) {
				MAGENTA_state_t state_in;
				std::copy(
					(uint8_t*)ciphertext_bytes.data() + offset,
					(uint8_t*)ciphertext_bytes.data() + offset + MAGENTA_BLOCK_SZ_BYTES,
					state_in.begin()
				);
				MAGENTA_state_t state_out = magenta.decrypt(
					state_in,
					keystore.get_key(user.employee_id)
				);
				std::copy(
					state_out.begin(),
					state_out.end(),
					(uint8_t*)plaintext_bytes.data() + offset
				);
			}
			string plaintext_b64 = Base64::Encode(plaintext_bytes);
			if (plaintext_b64.size() > 0) {
				send_tc_state(
					&tc_state_send,
					connected_socket,
					plaintext_b64.data(),
					plaintext_b64.size() * sizeof(plaintext_b64.data()[0]),
					0
				);
			}
		}		
		goto end_thread;
	}

send_error:
	send_tc_state(
		&tc_state_send, connected_socket, &error_code, sizeof(error_code), 0
	);

end_thread:
	{
		char const newline = '\n';
		send_tc_state(
			&tc_state_send, connected_socket, &newline, sizeof(newline), 0
		);
	}
	close(connected_socket);
	pthread_exit(NULL);
}