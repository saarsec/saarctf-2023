#pragma once

#include <cstdio>
#include <cinttypes>

#include <unordered_map>
using std::unordered_map;

#include <algorithm>
using std::pair;

#include <semaphore.h>

template<typename user_id_t, typename cryptokey_t>
class Keystore {
private:
	typedef unordered_map<user_id_t, cryptokey_t> keystore_map_t;
	keystore_map_t map;
	FILE* file_urandom;
	FILE* file_map;
	sem_t semaphore;

public:
	Keystore(void) {
		sem_init(&semaphore, 0, 1);
		file_urandom = fopen("/dev/urandom", "rb");
		if (file_urandom == NULL) {
			exit(1);
		}
		file_map = fopen("keystore.bin", "a+b");
		if (file_urandom == NULL) {
			exit(1);
		}
		load_map();
	}
	
	~Keystore(void) {
		fclose(file_urandom);
		fclose(file_map);
		sem_destroy(&semaphore);
	}

	Keystore(Keystore const&) = delete;
	Keystore& operator=(Keystore const&) = delete;
	Keystore(Keystore&&) = delete;
	Keystore& operator=(Keystore&&) = delete;

private:
	cryptokey_t gen_random_key(void) const {
		cryptokey_t key;
		size_t read = fread(key.data(), sizeof(key.data()[0]), key.size(), file_urandom);
		if (read != key.size()) {
			exit(1);
		}
		return key;
	}

	void load_map(void) {
		cryptokey_t key;
		size_t key_sz = sizeof(key.data()[0]) * key.size();
		size_t record_buf_sz = sizeof(user_id_t) + key_sz;
		uint8_t record_buf[record_buf_sz];

		while (fread(&record_buf, sizeof(record_buf), 1, file_map) == 1) {
			uint8_t* cursor = record_buf;
			
			user_id_t employee_id = *((user_id_t*)record_buf);
			cursor += sizeof(user_id_t);
			
			std::copy(cursor, cursor + key_sz, key.begin());
			cursor += key_sz;

			map[employee_id] = key;
		}
	}

	void append_employee_to_file(user_id_t const& employee_id, cryptokey_t const& key) const {
		fseek(file_map, 0, SEEK_END);
		{
			size_t written = fwrite(&employee_id, sizeof(employee_id), 1, file_map);
			if (written != 1) {
				exit(1);
			}
		}
		{
			size_t written = fwrite(key.data(), sizeof(key.data()[0]), key.size(), file_map);
			if (written != key.size()) {
				exit(1);
			}
		}
		fflush(file_map);
	}

public:
	cryptokey_t get_key(user_id_t employee_id) {
		sem_wait(&semaphore);
		typename keystore_map_t::const_iterator it = map.find(employee_id);
		if (it == map.end()) {
			cryptokey_t new_key = gen_random_key();
			map[employee_id] = new_key;
			append_employee_to_file(employee_id, new_key);
			sem_post(&semaphore);
			return new_key;
		} else {
			sem_post(&semaphore);
			return it->second;
		}
	}
};